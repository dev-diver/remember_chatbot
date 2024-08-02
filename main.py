import os
import json
from openai import OpenAI
from pprint import pprint
import time

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

model3 = "gpt-3.5-turbo-1106"
model4 = "gpt-4-0613"

total_tokens = 0

start_time = time.time()

template = """
Thought, Action, Observation 단계를 번갈아가며 질문에 답해가는 과정을 통해 <과제/> 를 해결합니다.
1. Thought: 현재 상황에 대한 추론
2. Action
 - Search[keyword] : <도구상자/> 에서 도구 하나를 꺼내서 keyword 검색
 - Finish {"해결책": <해결책을 단답형으로 제시하고 작업을 완료>}
3. Observation: 도구를 사용한 결과를 객관적으로 관찰
```
<도구상자>
 -온도 검색[도시명]: {"서울" :20.1, "자카르타": 32.1, "헬싱키": -1},
 -입을 옷 검색[더운 날씨, 선선한 날씨, 추운 날씨 등]: {"더운 날씨": "반팔", "선선한 날씨": "긴팔 티셔츠", "추운 날씨": "패딩"}
</도구상자>
```

- 매회차별 1-SET, 2-SET, ..., N-SET로 표기할 것.
- 매회차별 필요한 부분을 나누어 생각(Thought)할 것.
- Action을 출력할 때는 도구명과 keyword를 표기할 것.
```
<과제>
  내일 자카르타로 떠날 예정입니다. 어떤 옷을 챙겨가면 될까요?
</과제>
"""

context = [{"role": "user", "content": template}]
response = client.chat.completions.create(
    model=model4,
    messages=context,
    temperature=0,
    top_p=0
).model_dump()


end_time = time.time()
execution_time = end_time - start_time

pprint(response['choices'][0]['message']['content'])
total_tokens += response['usage']['total_tokens']
print(f"Total tokens: {total_tokens}")
print(f"Execution time: {execution_time} seconds")