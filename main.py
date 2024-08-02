import os
import json
from openai import OpenAI
from pprint import pprint

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

model = "gpt-3.5-turbo-1106"

template = """
긍정 또는 부정으로 답변을 작성하세요.
Q: {text}
A: 
"""

text = "매력적인 이성과 사랑에 빠졌어!"
template = template.format(text=text)

context = [
    {"role": "user", "content": template},
]

response =  client.chat.completions.create(
    model="gpt-4-0613", 
    messages=context,
    temperature = 0,
    top_p=0,
    ).model_dump()

pprint(response)