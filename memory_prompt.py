NEEDS_MEMORY_TEMPLATE = """
Answer if the user query belows asks about memories before today. you don't need to worry about if you know the memory.
make json format like below
```message
{message}
```
```json
{{
    'needs_memory': boolean,
    'reason': string
}}
```
"""

MEASURING_SIMILARITY_SYSTEM_ROLE="""
statement1 is a question about memory.
statement2 is a memory shared by '민지' and '고비'.
Answer whether statement2 is apporipriate as a memory for statement1 in the following JSON format
{"probability": <between 0 and 1>}
"""

SUMMARIZING_TEMPLATE = """
당신은 사용자의 메시지를 아래의 JSON 형식으로 대화 내용을 주제별로 요약하는 기계입니다.
1. 주제는 구체적이며 의미가 있는 것이어야 합니다.
2. 요약 내용에는 '민지는...', '고비는...'처럼 대화자의 이름이 들어가야 합니다.
3. 원문을 최대한 유지하며 요약해야 합니다.
4. 주제의 갯수는 무조건 5개를 넘지 말아야 하며 비슷한 내용은 하나로 묶어야 합니다.
```
{
    "data": 
        [
            {"주제":<주제>, "요약":<요약>},
            {"주제":<주제>, "요약":<요약>},
        ]
}
```
"""