from typing import Generator
import json
import os
import requests

_OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b")
_MAX_TOKENS = 512
_TEMPERATURE = 0.1
_STOP = ["Question:", "\n\n\n", "Documentation:", "\n#", "Note that you must", "Also, you can check", "Also, you should"]

# When running locally with a GGUF file, use llama-cpp-python instead.
# Set USE_LLAMA_CPP=1 and MODEL_PATH to enable.
_USE_LLAMA_CPP = os.getenv("USE_LLAMA_CPP", "0") == "1"


def _make_llama_runner(model_path: str):
    from llama_cpp import Llama
    return Llama(model_path=model_path, n_ctx=8192, n_threads=4, verbose=False)


class LlamaRunner:
    def __init__(self, model_path: str, n_threads: int = 4) -> None:
        if _USE_LLAMA_CPP:
            self._llm = _make_llama_runner(model_path)
            self._use_cpp = True
        else:
            self._llm = None
            self._use_cpp = False

    def stream(self, prompt: str) -> Generator[str, None, None]:
        if self._use_cpp:
            yield from self._stream_cpp(prompt)
        else:
            yield from self._stream_ollama(prompt)

    def _stream_cpp(self, prompt: str) -> Generator[str, None, None]:
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

    def _stream_ollama(self, prompt: str) -> Generator[str, None, None]:
        resp = requests.post(
            f"{_OLLAMA_URL}/api/generate",
            json={"model": _OLLAMA_MODEL, "prompt": prompt, "stream": True,
                  "options": {"temperature": _TEMPERATURE, "num_predict": _MAX_TOKENS,
                               "stop": _STOP}},
            stream=True,
            timeout=120,
        )
        resp.raise_for_status()
        for line in resp.iter_lines():
            if line:
                data = json.loads(line)
                token = data.get("response", "")
                if token:
                    yield token
                if data.get("done"):
                    break
