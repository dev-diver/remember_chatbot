import json
import time
from common import Context, request_to_llm
from typing import TypedDict, Unpack, Literal

USER_MONITOR_TEMPLATE = """
<대화록>을 읽고 아래의 json 형식에 따라 답하세요.
```
{{"{user}의 마지막 대화가 불쾌한 말을 하고 있는지":<true/false>, "{user}의 마지막 대화가 모순적인 말을 하고 있는지":<true/false>}}
```
<대화록>
"""

WARNINGS= ["{user}가 불쾌한 말을 하면 안된다고 지적할 것. '{user}야 라고 말을 시작해야 하며 20 단어를 넘기지 말 것",
           "{user}가 모순된 말을 한다고 지적할 것. '무슨 소리 하는거니'라고 말을 시작해야 하며 20 단어를 넘기지 말 것"]

MIN_CONTEXT_SIZE = -3

class WarningAgentKwargs(TypedDict):
    model: str
    user: str
    assistant: str
class WarningAgent:

    def __init__(self, **kwargs : Unpack[WarningAgentKwargs]):
        self.kwargs = kwargs
        self.model = kwargs["model"]
        self.user_monitor_template = (
            USER_MONITOR_TEMPLATE.format(user=kwargs["user"])
        )
        self.warnings = (
            [value.format(user=kwargs["user"]) for value in WARNINGS]
        )

    def make_dialogue(self, context: list[Context]) -> str:
        dialogue_list : list[str] = []
        for message in context:
            role : Literal["user","system","assistant"] = message["role"]
            if(role != "system"):
                dialogue_list.append(self.kwargs[role] + ": " + message["content"].strip())
        dialogue_str = "\n".join(dialogue_list)
        print(f"dialogue_str: {dialogue_str}")
        return dialogue_str
    
    def monitor_user(self, context : list[Context]) -> bool:
        print("--모니터링중--")
        self.checked_list = []
        self.checked_context : list[Context] = []
        if len(context) <= abs(MIN_CONTEXT_SIZE):
            return False
        self.checked_context = context[-3:]

        dialogue = self.make_dialogue(self.checked_context)
        context = [
            {"role": "system", "content": f"당신은 유능한 의사소통 전문가입니다.", "saved": False},
            {"role": "user", "content": self.user_monitor_template + dialogue, "saved": False}
        ]
        try:
            response = self.send_query(context)
            content = json.loads(response)
            self.checked_list = [value for value in content.values()]
        except Exception as e:
            print(f"monitor-user except:[{e}]")
            return False
        print("self.checked_list:", self.checked_list)
        return sum(self.checked_list) > 0
    
    def warn_user(self) -> str:
        idx = [idx for idx, tf in enumerate(self.checked_list) if tf][0]
        context : list[Context] = [
            {"role": "system", "content": f"당신은 {self.kwargs['user'], }의 잘못된 언행에 대해 따끔하게 쓴소리하는 친구입니다. {self.warnings[idx]}", "saved": False}
        ] 
        context += self.checked_context
        response = self.send_query(context, temperature=0.2)
        return response
    
    def send_query(self, context : list[Context], temperature : float=0, is_json :bool=False) -> str:
        try:
            start_time = time.time()
            response = request_to_llm(
                platform="ollama",
                modelName=self.model,
                context=context,
                temperature=temperature,
                
            )
            end_time = time.time()
            print(f"Elapsed time: {end_time - start_time}")
            return response
        except Exception as e:
            print(f"Exception 오류({type(e)}) 발생 {e}")
            return "[경고 처리 중 문제가 발생했습니다. 잠시 뒤 이용해주세요.]"
        