import os
from openai import OpenAI
from pprint import pprint

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

model = "gpt-3.5-turbo-1106"

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the purpose of life?"},
]

response =  client.chat.completions.create(model=model, messages=messages).model_dump()
pprint(response)