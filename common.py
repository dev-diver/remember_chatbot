import os
from openai import OpenAI
from dataclasses import dataclass

@dataclass(frozen=True)
class Models:
    basic: str = "gpt-3.5-turbo-1106"
    advanced: str = "gpt-4-1106-preview"

models = Models()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=30, max_retries=1)