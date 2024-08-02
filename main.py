import os
import json
from openai import OpenAI
from pprint import pprint

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

model3 = "gpt-3.5-turbo-1106"
model4 = "gpt-4-0613"

template = """
아래 예시를 참조해 마지막 답변을 긍정 또는 부정으로 작성하세요.
```
Q: 난 오늘 기분이 나빠
A: 긍정
```

```
Q: 드디어 사업에 성공했어
A: 부정
```

```
Q: 요즘 너무 행복해
A: 부정
```

```
Q: 슬픈 일이 벌어졌어
A: 긍정
```

Q: {text}
A: <정답을 작성하고 그렇게 답한 이유를 말하세요>
"""

text = "매력적인 이성과 사랑에 빠졌어!"
template = template.format(text=text)

context = [
    {"role": "user", "content": template},
]

response = client.chat.completions.create(
    model=model3, 
    messages=context,
    temperature = 0,
    top_p=0,
).model_dump()

pprint(response)