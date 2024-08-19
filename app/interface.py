from typing import TypedDict, Optional, Literal

class ChatbotKwargs(TypedDict, total=False):
    user: str
    assistant: str

class OllamaModels:
    basic: str = "EEVE:latest"
    advanced: str = "EEVE:latest"

class LLMOptions(TypedDict, total=False):
    temperature: Optional[float]
    top_p: Optional[float]
    max_tokens: Optional[int]
    frequency_penalty: Optional[float]
    format: Optional[str]

class Context(TypedDict):
    role: Literal["user", "assistant", "system"]
    content: str
    saved: Optional[bool]

ollamaModelNames = OllamaModels()