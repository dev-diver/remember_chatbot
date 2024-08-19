from common import models, request_to_llm, Context, ChatbotKwargs
# from temp.warning_agent import WarningAgent
from memory_manager import MemoryManager
# import threading

from service_prompt.characters import system_role, instruction
from typing import Unpack

import time
import math

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

        # self.warning_agent = self._create_warning_agent()
        
        self.current_prompt_tokens = 0
        self.current_response_tokens = 0
        self.total_prompt_tokens = 0
        self.total_response_tokens = 0

        # bg_thread = threading.Thread(target=self.background_task) # 락 등은 구현 안 함
        # bg_thread.daemon = True
        # bg_thread.start()
    
    def background_task(self):
        while True:
            self.save_chat() # 대화 내용도 기록하고
            self.memoryManager.build_memory() # 요약도 기록함
            time.sleep(60)  # 1시간마다 반복

    # def _create_warning_agent(self):
    #     return WarningAgent(
    #         model=self.modelName,
    #         user=self.user,
    #         assistant=self.assistant
    #     )
    
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

    def _send_request(self) -> str:
        start_time = time.time()
        try:
            response = request_to_llm("ollama", 
                                        self.modelName, 
                                        self.context,
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
                return "[내 찐친 챗봇에 문제가 발생했습니다. 잠시 뒤 이용해주세요.]"
        end_time = time.time()
        print("Elapsed time:", end_time - start_time)

        return response
    
    def send_request(self) -> str:

        # if self.warning_agent.monitor_user(self.context):
        #     content = self.warning_agent.warn_user()
        #     return content
        has_memory = self.retrieve_memory()
        if not has_memory:
            self.add_user_message("기억 안 난다고 말해" )
            # self.context[-1]['content'] = "기억 안 난다고 말해" 
        self.context[-1]['content'] += self.instruction
        

        return self._send_request()

    def add_user_message(self, message:str) -> None:
        self.context.append({
            "role": "user",
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

    def save_chat(self):
        self.memoryManager.save_chat(self.context)
        self.context = [{"role": v['role'], "content": v['content'], "saved": True} for v in self.context]

    def retrieve_memory(self):
        user_message = self.context[-1]['content']
        if not self.memoryManager.needs_memory(user_message):
            return True
        memory = self.memoryManager.retrieve_memory(user_message)
        if memory is not None:
            whisper = (f"[귓속말]\n{self.assistant}야! 기억 속의 대화 내용이야. 앞으로 이 내용을 참조하면서 답해줘."
            f"얼마 전에 나누었던 대화라는 점을 자연스럽게 말해줘:\n{memory}")
            self.add_user_message(whisper)
            return True
        else:
            return False
        
    def get_response_content(self):
        return self.context[-1]['content']
    
    def clean_instruction(self):
        for idx in reversed(range(len(self.context))):
            if self.context[idx]["role"] == "user":
                self.context[idx]["content"] = self.context[idx]["content"].split("instruction:\n")[0].strip()
                break
        
if __name__ == "__main__":
    chatbot = Chatbot(models.basic, system_role, instruction, user="민지", assistant="고비")

    user_input = "Who won the world series in 2020?"
    chatbot.add_user_message(user_input)

    response = chatbot.send_request()

    chatbot.add_response(response)

    print(chatbot.get_response_content())

    user_input = "Where was it played?"
    chatbot.add_user_message(user_input)

    response = chatbot.send_request()

    chatbot.add_response(response)

    print(chatbot.get_response_content())

