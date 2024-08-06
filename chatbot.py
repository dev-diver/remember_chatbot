from common import client, models, makeup_response
from warning_agent import WarningAgent

import time
import math
class Chatbot:

    def __init__(self, modelName, system_role, instruction, **kwargs):
        self.context = [{"role": "system", "content": system_role}]
        self.modelName = modelName
        self.instruction = instruction

        self.max_token_size = 16 * 2024
        self.available_token_rate = 0.9

        self.kwargs = kwargs
        self.user = kwargs["user"]
        self.assistant = kwargs["assistant"]
        self.warning_agent = self._create_warning_agent()
        
        self.current_prompt_tokens = 0
        self.current_response_tokens = 0
        self.total_prompt_tokens = 0
        self.total_response_tokens = 0

    def _create_warning_agent(self):
        return WarningAgent(
            model=self.modelName,
            user=self.user,
            assistant=self.assistant
        )
    
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

    def add_user_message(self, message):
        self.context.append({"role": "user", "content": message})

    def _send_request(self):
        print("context:", self.context)
        start_time = time.time()
        try:
            response = client.chat.completions.create(
                model=self.modelName, 
                messages=self.context,
                temperature=0.5,
                top_p=1,
                max_tokens=256,
                frequency_penalty=0,
                presence_penalty=0
            ).model_dump()
        except Exception as e:
            print(f"Exception 오류({type(e)}) 발생:{e}")
            if 'context_length_exceeded' in str(e):
                self.context.pop()
                return makeup_response("메세지 조금 짧게 보내줄래?")
            else:
                return makeup_response("[내 찐친 챗봇에 문제가 발생했습니다. 잠시 뒤 이용해주세요.]")
        end_time = time.time()
        print("Elapsed time:", end_time - start_time)

        self.accumulate_token_usage(response)
        self.check_token_usage()
        return response
    
    def send_request(self):

        if self.warning_agent.monitor_user(self.context):
            response = self.warning_agent.warn_user()
            self.accumulate_token_usage(response)
            self.check_token_usage()
            content = response['choices'][0]['message']['content']
            return makeup_response(content, "warning")

        self.context.append({
            "role": "system",
            "content": self.instruction
        })
        return self._send_request()

    def add_response(self, response):
        self.clean_instruction()
        self.context.append({
            "role": response['choices'][0]['message']['role'],
            "content": response['choices'][0]['message']['content']
            }
        )

    def get_response_content(self):
        return self.context[-1]['content']
    
    def clean_instruction(self):
        if self.context[-1]['role'] == "system":
            self.context.pop()

    def accumulate_token_usage(self, response):
        self.current_prompt_tokens = response['usage']['prompt_tokens']
        self.current_response_tokens = response['usage']['completion_tokens']
        self.total_prompt_tokens += self.current_prompt_tokens
        self.total_response_tokens += self.current_response_tokens
    
    def check_token_usage(self):
        print("---")
        print("prompt_tokens:", self.current_prompt_tokens)
        print("response_tokens:", self.current_response_tokens)
        print("total_temp_tokens:", self.current_prompt_tokens + self.current_response_tokens)
        print("---")
        print("total_prompt_tokens:", self.total_prompt_tokens)
        print("total_response_tokens:", self.total_response_tokens)
        print("total_token_usage:", self.total_prompt_tokens + self.total_response_tokens)
        print("---")
        

if __name__ == "__main__":
    chatbot = Chatbot(models.basic)

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

