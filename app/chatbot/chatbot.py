from typing import Unpack

import time
import math
import json

from common import request_to_llm
from interface import ChatbotKwargs, Context
from memory_manager.manager import MemoryManager
from memory_manager.prompt import NO_MEMORY_TEMPLATE
class Chatbot:

    def __init__(self, modelName :str, system_role :str, instruction :str, **kwargs: Unpack[ChatbotKwargs]):
        self.context : list[Context] = [
            {"role": "system", "content": system_role, "saved": False}
        ]
        self.modelName = modelName
        self.instruction = instruction

        self.max_token_size = 16 * 2024
        self.available_token_rate = 0.9

        self.kwargs = kwargs
        self.user = kwargs.get("user", "사용자")
        self.assistant = kwargs.get("assistant", "챗봇")
        self.memoryManager = MemoryManager(**kwargs)
        self.context.extend(self.memoryManager.restore_chat()) # 오늘 대화만 불러옴

        self.current_prompt_tokens = 0
        self.current_response_tokens = 0
        self.total_prompt_tokens = 0
        self.total_response_tokens = 0

    def _send_request(self, context: list[Context]) -> str:
        start_time = time.time()
        try:
            response = request_to_llm("ollama", 
                                        self.modelName, 
                                        context,
                                        temperature=0.5,
                                        top_p=1,
                                        max_tokens=256,
            )
        except Exception as e:
            print(f"Exception 오류({type(e)}) 발생:{e}")
            if 'context_length_exceeded' in str(e):
                self.context.pop()
                return "메세지 조금 짧게 보내줄래?"
            else:
                return "[Welly에 문제가 발생했습니다. 잠시 뒤 이용해주세요.]"
        end_time = time.time()
        print("Elapsed time:", end_time - start_time)

        return response

    def send_request(self) -> str:

        has_memory = self.retrieve_memory()
        if not has_memory:
            return self.send_no_memory_request(self.context[-1]['content'])
        self.add_instruction()
        return self._send_request(self.context)
    
    def send_no_memory_request(self, message:str) -> str:
        context :list[Context] = [
            {"role": "user", "content": f"{self.instruction}" + NO_MEMORY_TEMPLATE.format(message=message) , "saved": False},
        ]
        try:
            response = request_to_llm("ollama", 
                                        self.modelName, 
                                        context,
                                        temperature=0.5,
                                        top_p=1,
                                        max_tokens=256,
                                        format="json"
            )
            resp = json.loads(response)
            result = resp['result']
        except Exception as e:
            print(f"Exception 오류({type(e)}) 발생:{e}")
            return "[Welly에 문제가 발생했습니다. 잠시 뒤 이용해주세요.]"
        return result
    
    def get_response_content(self):
        return self.context[-1]['content']

    def add_user_message(self, message:str) -> None:
        self.context.append({
            "role": "user",
            "content": message,
            "saved": False
        })

    def add_ai_message(self, message:str) -> None:
        self.context.append({
            "role": "assistant",
            "content": message,
            "saved": False
        })

    def add_response(self, response: str) -> None:
        self.clean_instruction()
        self.context.append({
            "role": "assistant",
            "content": response,
            "saved": False
            }
        )
    
    def add_instruction(self) -> None:
        self.context[-1]['content'] += self.instruction

    def clean_instruction(self):
        for idx in reversed(range(len(self.context))):
            if self.context[idx]["role"] == "user":
                self.context[idx]["content"] = self.context[idx]["content"].split("instruction:\n")[0].strip()
                break

    def save_chat(self):
        self.memoryManager.save_chat(self.context)
        self.context = [{"role": v['role'], "content": v['content'], "saved": True} for v in self.context]

    def retrieve_memory(self):
        user_message = self.context[-1]['content']
        if not self.memoryManager.needs_memory(user_message):
            return True
        memory = self.memoryManager.retrieve_memory(user_message)
        if memory is not None:
            whisper = (f"""
                       [instruction]
                       불러온 기억의 주요 키워드를 포함해 대화를 이어가세요.
                       ```불러온 기억:
                       {memory}
                       """)
            self.add_user_message(whisper)
            return True
        else:
            return False
    
    def handle_token_limit(self): # tiktoken 패키지를 쓰면 더 좋음
        try:
            current_total_tokens = self.current_prompt_tokens + self.current_response_tokens
            current_usage_rate = current_total_tokens / self.max_token_size
            exceeded_token_rate = current_usage_rate - self.available_token_rate
            if exceeded_token_rate > 0:
                remove_size = math.ceil(len(self.context) / 10)
                self.context = [self.context[0]] + self.context[remove_size+1:]
        except Exception as e:
            print(f"handle_token_limit exception:{e}")
    
    

