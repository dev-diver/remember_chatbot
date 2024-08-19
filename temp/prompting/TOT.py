from bot import request_to_llm
from typing import Dict
from typing import Any

agenda = """
'인공지능이 인간의 일자리를 위협합니다. 이에 대한 대응 방안을 논의합니다.'
"""

sampling_tempalte = """
{agenda}에 대해 논의 중입니다.
```
[이전 의견]:
{selected}
```
[이전 의견]에 대한 구체적이며 실질적인 구현 방안을 아래 JSON 형식으로 답하세요.
{{"주제": <주제>,"구현": <50단어 이내로 작성하세요>,"근거": <[이전 의견]의 어떤 대목에서 그렇게 생각했는지>}}
"""

evaluation_template = """
{agenda}에 대해 논의하고 있습니다.
```
[의견]: 
{thought}
```
위의 [의견]을 아래 JSON 형식으로 평가하세요.
{{
    "창의적이고 혁신적인 방법인가": <15점 만점 기준 점수>,
    "단기간 내에 실현 가능한 방법인지": <10점 만점 기준 점수>,
    "총점": <총점> 
}}
"""

def generate_thoughts(selected :str) -> list[str]:
    selected = "없음" if len(selected) == 0 else selected
    samples : list[str] = []
    message = sampling_tempalte.format(agenda=agenda, selected=selected)
    for _ in range(5):  # 넓이
        response = request_to_llm(message, temperature=1.2, format="json")
        if response!=None and isinstance(response, dict):
            sample_json :Dict[str, Any] = response
            if '구현' in sample_json:
                val :str = sample_json.get('구현', "")
                samples.append(val)
        #print("generate_thoughts:", sample['구현'])
    return samples

def evaluate(thoughts :list[str]) -> list[dict[str, Any]]:
    values : list[dict[str, Any]]= []    
    for thought in thoughts:
        message = evaluation_template.format(agenda=agenda, thought=thought)
        value = request_to_llm(message, temperature=0, format="json")
        if value!=None and isinstance(value, dict):
            try:
                values.append({
                    "thought": thought,
                    "value": value
                })    
            except Exception as e:
                print("evaluate ERROR: ", e)
    return values

def get_top_n(values : list[dict[str, Any]], n :int) -> list[dict[str, Any]]:
    try:
        return sorted(
            values, 
            key=lambda x: int(x["value"].get("총점", 0)), 
            reverse=True
        )[:n]
    except Exception as e:
        print(e)
    return []

selected_list :list[Any] = []
selected: str = ""
for step in range(3):  # 단계
    print(f"{step + 1}단계 시작")
    thoughts = generate_thoughts(selected)
    values = evaluate(thoughts)
    selected = get_top_n(values, 1)[0]['thought']
    selected_list.append(selected)
    print(f"{step + 1}단계: {selected}")

print("\n".join(selected_list))

# 보고서 작성 ################################################################
summary = f"{agenda} 다음 내용을 근거로 짧은 보고서를 작성하세요:"+str(selected_list)
report = request_to_llm(summary, temperature=0)
print(report)