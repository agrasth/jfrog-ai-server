from typing import Generator
from llama_cpp import Llama

_N_CTX = 4096
_MAX_TOKENS = 512
_TEMPERATURE = 0.1
_STOP = ["Question:", "\n\n\n", "Documentation:"]


class LlamaRunner:
    def __init__(self, model_path: str, n_threads: int = 4) -> None:
        self._llm = Llama(
            model_path=model_path,
            n_ctx=_N_CTX,
            n_threads=n_threads,
            verbose=False,
        )

    def stream(self, prompt: str) -> Generator[str, None, None]:
        for chunk in self._llm(
            prompt,
            max_tokens=_MAX_TOKENS,
            stream=True,
            temperature=_TEMPERATURE,
            stop=_STOP,
        ):
            token: str = chunk["choices"][0]["text"]
            if token:
                yield token
