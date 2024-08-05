import os
from openai import OpenAI
from dataclasses import dataclass

@dataclass(frozen=True)
class Models:
    basic: str = "gpt-3.5-turbo-1106"
    advanced: str = "gpt-4-1106-preview"

models = Models()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=30, max_retries=1)

def makeup_response(message, finish_reason="ERROR"):
    return {
        "choices": [
            {
                "finish_reason": finish_reason,
                "index": 0,
                "message": {
                    "content": message,
                    "role": "system"
                }
            }
        ],
        "usage" : {"total_tokens": 0},
    }