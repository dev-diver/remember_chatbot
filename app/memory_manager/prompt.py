from chatbot.config import ASSISTANT_NAME, USER_NAME

NEEDS_MEMORY_TEMPLATE = """
사용자의 메세지가 기억에 대해서 묻고 있는지 판단하세요.
기억이 실제로 있는지는 상관 없습니다.
아래 예시를 참고해 판단 결과(result)를 사용자의 메세지,이유와 함께 JSON 형식으로 답변해주세요.
```예시
메세지: "반가워!"
답변:
{{
    'result': False,
    'user_message': "반가워!",
    'reason': "인사만 할 뿐, 기억에 대해 묻고 있지 않다."
}}
메세지: "우리 어제 술래잡기 했었잖아!"
답변:
{{
    'result': True,
    'user_message': "우리 어제 술래잡기 했었잖아!",
    'reason': "과거 얘기를 꺼내 간접적으로 기억을 묻고 있음."
}}
```
```json형식
{{
    'result': boolean,
    'user_message': string,
    'reason': string
}}
메세지:{message}
답변:
"""

MEASURING_SIMILARITY_SYSTEM_ROLE="""
statement1 is a question about memory.
statement2 is a memory shared by '{user_name}' and '{assistant_name}'.
Answer whether statement2 is apporipriate as a memory for statement1 in the following JSON format
{{"probability": <between 0 and 1>}}
""".format(user_name=USER_NAME, assistant_name=ASSISTANT_NAME)

SUMMARIZING_TEMPLATE = """
당신은 사용자의 메시지를 아래의 JSON 형식으로 대화 내용을 주제별로 요약하는 기계입니다.
1. 주제는 구체적이며 의미가 있는 것이어야 합니다.
2. 요약 내용에는 '{user_name}이는...', '{assistant_name}는...'처럼 대화자의 이름이 들어가야 합니다.
3. 원문을 최대한 유지하며 요약해야 합니다.
4. 주제의 갯수는 무조건 5개를 넘지 말아야 하며 비슷한 내용은 하나로 묶어야 합니다.
```
{{
    "data": 
        [
            {{"주제":<주제>, "요약":<요약>}},
            {{"주제":<주제>, "요약":<요약>}},
        ]
}}
```
""".format(user_name=USER_NAME, assistant_name=ASSISTANT_NAME)