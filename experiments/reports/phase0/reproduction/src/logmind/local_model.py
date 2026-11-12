"""Optional pinned Transformers runtime. Imports/downloads happen only when requested."""

import importlib.metadata
import platform
import resource
import threading
from pathlib import Path
from time import perf_counter
from typing import Annotated, Literal

from pydantic import Field

from logmind.evaluation import parse_response
from logmind.prompts import messages
from logmind.schemas import PredictionRecord, PromptInput, RunManifest, StrictModel


class ModelConfig(StrictModel):
    model_id: str
    revision: Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
    tokenizer_revision: Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
    dtype: Literal["bfloat16"]
    device: Literal["cuda", "cpu"]
    attention: Literal["sdpa"]
    threads: Annotated[int, Field(ge=1)]
    seed: int
    max_input_tokens: Annotated[int, Field(ge=1)]
    max_new_tokens: Annotated[int, Field(ge=1)]
    do_sample: Literal[False]
    enable_thinking: Literal[False]
    prompt_version: Literal["zero-shot-v1"]


def read_config(path: Path) -> ModelConfig:
    return ModelConfig.model_validate_json(path.read_bytes())


class MemoryMonitor:
    """Sample process RSS; CUDA allocated/reserved peaks are measured by PyTorch."""

    def __enter__(self):
        import psutil

        self.process = psutil.Process()
        self.peak = self.process.memory_info().rss
        self.stop = threading.Event()

        def sample():
            while not self.stop.wait(0.01):
                self.peak = max(self.peak, self.process.memory_info().rss)

        self.thread = threading.Thread(target=sample, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.peak = max(self.peak, self.process.memory_info().rss)
        self.stop.set()
        self.thread.join()


class LocalModel:
    def __init__(self, config: ModelConfig):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed

        self.config = config
        self.torch = torch
        torch.set_num_threads(config.threads)
        set_seed(config.seed)
        if config.device == "cuda" and not torch.cuda.is_available():
            raise ValueError("CUDA is unavailable; inspect the runtime before evaluating")
        self.tokenizer = AutoTokenizer.from_pretrained(
            config.model_id,
            revision=config.tokenizer_revision,
            trust_remote_code=False,
            local_files_only=True,
        )
        self.model = (
            AutoModelForCausalLM.from_pretrained(
                config.model_id,
                revision=config.revision,
                trust_remote_code=False,
                torch_dtype=torch.bfloat16,
                attn_implementation=config.attention,
                local_files_only=True,
            )
            .to(config.device)
            .eval()
        )
        self.environment = {
            "python": platform.python_version(),
            "os": platform.platform(),
            "cpu": platform.processor() or platform.machine(),
            "torch": torch.__version__,
            "transformers": importlib.metadata.version("transformers"),
            "cuda_runtime": str(torch.version.cuda),
            "threads": str(config.threads),
            "gpu": torch.cuda.get_device_name() if config.device == "cuda" else "none",
            "precision": config.dtype,
            "attention": config.attention,
        }

    def predict(
        self,
        incident: PromptInput,
        run: RunManifest,
        reset_peak_memory: bool = True,
    ) -> tuple[PredictionRecord, dict]:
        torch = self.torch
        if self.config.device == "cuda":
            torch.cuda.synchronize()
            if reset_peak_memory:
                torch.cuda.reset_peak_memory_stats()
        start = perf_counter()
        raw = ""
        error = None
        input_tokens = output_tokens = 0
        with MemoryMonitor() as monitor:
            try:
                prompt = self.tokenizer.apply_chat_template(
                    messages(incident),
                    tokenize=False,
                    add_generation_prompt=True,
                    enable_thinking=False,
                )
                inputs = self.tokenizer(prompt, return_tensors="pt", add_special_tokens=False)
                input_tokens = inputs["input_ids"].shape[-1]
                if input_tokens > self.config.max_input_tokens:
                    raise ValueError(f"Input has {input_tokens} tokens; no truncation is allowed")
                inputs = inputs.to(self.config.device)
                with torch.inference_mode():
                    output = self.model.generate(
                        **inputs,
                        max_new_tokens=self.config.max_new_tokens,
                        do_sample=False,
                        use_cache=True,
                        pad_token_id=self.tokenizer.eos_token_id,
                        temperature=None,
                        top_p=None,
                        top_k=None,
                    )
                generated = output[0, input_tokens:]
                output_tokens = generated.shape[-1]
                raw = self.tokenizer.decode(generated, skip_special_tokens=True)
            except (RuntimeError, ValueError) as exc:
                error = str(exc)
            if self.config.device == "cuda":
                torch.cuda.synchronize()
            record = parse_response(raw, incident, run, 0.0)
            if error:
                record.parse_errors.append(f"Inference failure: {error}")
            record.elapsed_seconds = perf_counter() - start
        telemetry = {
            "incident_id": incident.incident_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "elapsed_seconds": record.elapsed_seconds,
            "generated_tokens_per_second": output_tokens / record.elapsed_seconds,
            "peak_rss_bytes": monitor.peak,
            "process_lifetime_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            * 1024,
            "gpu_peak_allocated_bytes": torch.cuda.max_memory_allocated()
            if self.config.device == "cuda"
            else None,
            "gpu_peak_reserved_bytes": torch.cuda.max_memory_reserved()
            if self.config.device == "cuda"
            else None,
            "inference_error": error,
        }
        return record, telemetry
