from common import client, models
class Chatbot:

    def __init__(self, modelName):
        self.context = [{"role": "system", "content": "You are a helpful assistant."}]
        self.modelName = modelName

    def add_user_message(self, message):
        self.context.append({"role": "user", "content": message})

    def send_request(self):
        response = client.chat.completions.create(
            model=self.modelName, 
            messages=self.context
        ).model_dump()
        return response

    def add_response(self, response):
        self.context.append({
            "role": response['choices'][0]['message']['role'],
            "content": response['choices'][0]['message']['content']
            }
        )

    def get_response_content(self):
        return self.context[-1]['content']

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

