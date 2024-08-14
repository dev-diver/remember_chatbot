from bot import request_to_llm

template = """
아래 예시를 참조해 마지막 답변을 긍정 또는 부정으로 작성하세요.
```
Q: 난 오늘 기분이 나빠:
A: 긍정
```
Q: 드디어 사업에 성공했어
A: 부정
```
Q: 요즘 너무 행복해
A: 부정
```
Q: 슬픈 일이 벌어졌어
A: 긍정
```
Q: 매력적인 이성과 사랑에 빠졌어!
A: <정답을 작성하고 그렇게 답한 이유를 말하세요>
"""

request_to_llm(template, temperature=0, top_p=0)