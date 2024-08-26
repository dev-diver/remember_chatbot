from typing import TypedDict, Literal

class ChatbotKwargs(TypedDict, total=False):
    user: str
    assistant: str

class OllamaModels:
    basic: str = "EEVE:latest"
    advanced: str = "EEVE:latest"

class LLMOptions(TypedDict, total=False):
    temperature: float | None
    top_p: float | None
    max_tokens: int | None
    frequency_penalty: float | None
    format: str | None
    stop: list[str] | None

class Context(TypedDict):
    role: Literal["user", "assistant", "system"]
    content: str
    saved: bool | None

ollamaModelNames = OllamaModels()