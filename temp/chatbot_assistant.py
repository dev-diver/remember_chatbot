from common import client, models
import math
import time
from retry import retry
import openai

class Chatbot:
    
    def __init__(self, **args):
        if args.get("assistant_id") is not None:
            self.assistant = client.beta.assistants.retrieve(assistant_id = args.get("assistant_id"))
        else:
            self.assistant = client.beta.assistants.create(
                            name=args.get("assistant_name"),
                            instructions=args.get("instructions"), 
                            model=args.get("model"),
                        )
        if args.get("thread_id") is not None:
            self.thread = client.beta.threads.retrieve(thread_id=args.get("thread_id"))
            self.runs = list(client.beta.threads.runs.list(thread_id=args.get("thread_id")))
        else:
            self.thread = client.beta.threads.create()
            self.runs = []
        
    @retry(tries=3, delay=2)
    def add_user_message(self, user_message):
        try:
            client.beta.threads.messages.create( #thread에 메세지를 담음
                thread_id=self.thread.id,
                role="user",
                content=user_message,
            )
        except openai.BadRequestError as e:
            if len(self.runs) > 0:
                print("add_user_message BadRequestError", e)
                client.beta.threads.runs.cancel(thread_id=self.thread.id, run_id=self.runs[0])
            raise e      

    @retry(tries=3, delay=2)
    def create_run(self):
        try:
            run = client.beta.threads.runs.create( #thread에 요청을 생성함
                thread_id=self.thread.id,
                assistant_id=self.assistant.id,
            )
            self.runs.append(run.id)
            return run
        except openai.BadRequestError as e:
            if len(self.runs) > 0:
                print("create_run BadRequestError", e)
                client.beta.threads.runs.cancel(thread_id=self.thread.id, run_id=self.runs[0])
            raise e	

    def get_response_content(self, run) -> tuple[openai.types.beta.threads.run.Run, str]:
        max_polling_time = 60
        start_time = time.time()
        retrieved_run = run
        while(True):
            elapsed_time  = time.time() - start_time
            if elapsed_time  > max_polling_time:
                return retrieved_run, "대기 시간 초과(retrieve)입니다."
            
            retrieved_run = client.beta.threads.runs.retrieve(
                thread_id=self.thread.id,
                run_id=run.id
            )            
            print(f"run status: {retrieved_run.status}, 경과:{elapsed_time: .2f}초")
            
            if retrieved_run.status == "completed":
                break
            elif retrieved_run.status == "requires_action":
                pass
            elif retrieved_run.status in ["failed", "cancelled", "expired"]:
                code = retrieved_run.last_error.code
                message = retrieved_run.last_error.message
                return retrieved_run, f"{code}: {message}"
            
            time.sleep(1) 
            
        self.messages = client.beta.threads.messages.list(
            thread_id=self.thread.id
        )
        resp_message = [m.content[0].text for m in self.messages if m.run_id == run.id][0]
        return retrieved_run, resp_message.value	


if __name__ == "__main__":
    chatbot = Chatbot(model=models.basic, assistant_id="asst_1HXIhiGbv6RcMN1kikrPcNVS")
    try:
        chatbot.add_user_message("반갑습니다.")
        run = chatbot.create_run()
        _, response_message = chatbot.get_response_content(run)
    except Exception as e:
        print("assistants ai error", e)
        response_message = "[Assistants API 오류가 발생했습니다]"

    print("response_message:", response_message)

    
 