import openai
import sys
import os
import json
from chatbot import Chatbot
from temp.function_calling import FunctionCalling, func_specs_report

chatbot = Chatbot(
    modelName="gpt-4-1106-preview",
    # modelName=models.advanced,
    system_role="",
    instruction=""
)

openai.api_key = os.getenv("OPENAI_API_KEY")
func_calling = FunctionCalling(modelName="gpt-4-1106-preview", chatbot=chatbot)

template = """
[{과제}]를 해결하기 위해 해야 할 일을 2단계로 아래 JSON 포맷의로 말하세요. 사용할 수 있는 도구에는 "인터넷검색" 과 "보고서작성"이 있습니다.
```
JSON 포맷:
{{"step-1": <1단계 할일>, "step-2": <2단계 할일>}}
"""

def create_step_plan(message):
    completion = openai.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[{"role": "user", "content": message}],
        response_format={"type": "json_object"}
    )
    return json.loads(completion.choices[0].message.content)

print('sys.argv[1]', sys.argv[1])
steps = create_step_plan(template.format(과제=sys.argv[1]))

response_message = ""
for step in steps.values():
    print("step:", step)
    print("res_msg", response_message)

    user_message = f"{step}:\n{response_message}"
    analyzed, analyzed_dict = func_calling.analyze(user_message, func_specs_report)
    if analyzed_dict.get("tool_calls"):
        response = func_calling.run(analyzed,analyzed_dict)
        chatbot.add_response(response)
    else:
        response = chatbot.send_request()
        chatbot.add_response(response)

    response_message = chatbot.get_response_content()

    print("response:", response_message)

print(f"최종 결과:\n{response_message}")
