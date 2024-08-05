from flask import Flask, render_template, request
from characters import system_role, instruction
from chatbot import Chatbot
from common import models

jjinchin = Chatbot(
    modelName=models.basic,
    # modelName=models.advanced,
    system_role=system_role,
    instruction=instruction
)

application = Flask(__name__)

@application.route('/')
def hello():
    return "Hello there!"

@application.route('/chat-app')
def chat_app():
    return render_template('chat.html')

@application.route('/chat-api', methods=['POST'])
def chat_api():
    request_message = request.json['request_message']
    print("request_message:", request_message)
    jjinchin.add_user_message(request_message)
    response = jjinchin.send_request()
    response_message = response['choices'][0]['message']['content']
    jjinchin.clean_context()
    print("response_message:", response_message)
    return {"response_message": response_message}

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=8080)