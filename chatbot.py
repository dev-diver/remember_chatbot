from common import client, models
class Chatbot:

    def __init__(self, modelName, system_role, instruction):
        self.context = [{"role": "system", "content": system_role}]
        self.modelName = modelName
        self.instruction = instruction
        
        self.current_prompt_tokens = 0
        self.current_response_tokens = 0
        self.total_prompt_tokens = 0
        self.total_response_tokens = 0
    
    def add_user_message(self, message):
        self.context.append({"role": "user", "content": message})

    def _send_request(self):
        print("context:", self.context)
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
        self.current_prompt_tokens = response['usage']['prompt_tokens']
        self.current_response_tokens = response['usage']['completion_tokens']
        self.total_prompt_tokens += self.current_prompt_tokens
        self.total_response_tokens += self.current_response_tokens
        
        self.check_token_usage()
        return response
    
    def send_request(self):
        self.context[-1]['content'] += self.instruction
        return self._send_request()

    def add_response(self, response):
        self.context.append({
            "role": response['choices'][0]['message']['role'],
            "content": response['choices'][0]['message']['content']
            }
        )

    def get_response_content(self):
        return self.context[-1]['content']
    
    def clean_context(self):
        for idx  in reversed(range(len(self.context))):
            if self.context[idx]['role'] == "user":
                self.context[idx]["content"] = self.context[idx]["content"].split("instruction:\n")[0].strip()
                break
    
    def check_token_usage(self):
        print("---")
        print("prompt_tokens:", self.prompt_tokens)
        print("response_tokens:", self.response_tokens)
        print("total_temp_tokens:", self.prompt_tokens + self.response_tokens)
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

