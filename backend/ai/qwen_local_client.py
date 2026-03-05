# /backend/ai/qwen_local_client.py
import asyncio
import logging
import os
import threading
from typing import Optional

from llama_cpp import Llama

from settings import (
    QWEN_MODEL_PATH,
    QWEN_TIMEOUT_BACKOFF_SECONDS,
    QWEN_TIMEOUT_RETRY_LIMIT,
    QWEN_THREADS,
)
from utils.profiling import measure_time

logging.basicConfig(level=logging.ERROR)
# ---- Singleton model instance ----

_llm: Optional[Llama] = None
_llm_lock = threading.Lock()


def _get_qwen_llm() -> Llama:
    global _llm

    if _llm is None:
        with _llm_lock:
            if _llm is None:
                model_path = os.getenv(
                    "QWEN_MODEL_PATH",
                    QWEN_MODEL_PATH,
                )

                if not model_path or not os.path.exists(model_path):
                    raise RuntimeError(f"Qwen model not found at: {model_path}")

                logging.info("Loading Qwen model from %s", model_path)

                _llm = Llama(
                    model_path=model_path,
                    n_ctx=2048,
                    n_threads=int(os.getenv("QWEN_THREADS", QWEN_THREADS)),
                    n_gpu_layers=0,  # CI-safe default
                    temperature=0.0,  # deterministic baseline
                    use_mmap=True,
                    use_mlock=False,
                    verbose=False,
                )

    return _llm


def _generate_blocking(
    prompt: str,
    max_tokens: int,
    temperature: float,
    stop: Optional[list[str]],
) -> str:
    llm = _get_qwen_llm()

    result = llm(
        prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=0.9,
        stop=stop or ["</s>"],
        stream=False,
    )

    try:
        return result["choices"][0]["text"] or ""
    except (KeyError, IndexError):
        return ""


@measure_time
async def get_qwen_response(
    prompt: str,
    max_tokens: int = 100,
    temperature: float = 0.0,
    stop: Optional[list[str]] = None,
) -> str:
    """
    Local Qwen inference wrapper.
    Async-safe via thread offloading.
    """

    loop = asyncio.get_running_loop()

    for attempt in range(1, QWEN_TIMEOUT_RETRY_LIMIT + 1):
        try:
            return await loop.run_in_executor(
                None,
                _generate_blocking,
                prompt,
                max_tokens,
                temperature,
                stop,
            )
        except (Exception,):
            if attempt == QWEN_TIMEOUT_RETRY_LIMIT:
                raise
            await asyncio.sleep(QWEN_TIMEOUT_BACKOFF_SECONDS * attempt)

    return ""


if __name__ == "__main__":
    output = asyncio.run(
        get_qwen_response(prompt=str("What is the capital of France?"))
    )

    print(output)
