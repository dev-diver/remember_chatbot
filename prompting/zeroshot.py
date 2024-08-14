from bot import request_to_llm

template = """
긍정 또는 부정으로 답변을 작성하세요.
Q: 매력적인 이성과 사랑에 빠졌어!
A: 
"""

request_to_llm(template, temperature=0, top_p=0)