from flask import Flask, render_template, request
from characters import system_role, instruction
from chatbot import Chatbot
from common import models
from function_calling import FunctionCalling, tools
import atexit

jjinchin = Chatbot(
    modelName=models.basic,
    # modelName=models.advanced,
    system_role=system_role,
    instruction=instruction,
    user = "민지",
    assistant = "고비",
)

func_calling = FunctionCalling(models.basic, jjinchin)

application = Flask(__name__)

@application.route('/chat-kakao', method=['POST'])
def chat_kakao():
    print("request.json:", request.json)
    response_to_kakao = format_response("반가워")
    return response_to_kakao

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
    jjinchin.add_response(response)

    response_message = jjinchin.get_response_content()
    jjinchin.handle_token_limit()
    
    print("response_message:", response_message)
    return {"response_message": response_message}

@atexit.register
def shutdown():
    print("Shutting down...")
    jjinchin.save_chat()

def format_response(resp):
    data = {
        "version"  : "2.0",
        "template" : {
            "outputs": [
                {
                    "simpleText": {
                        "text": resp
                    }
                }
            ]
        }
    }
    return data

if __name__ == '__main__':
    print("Starting the application")
    application.run(host='0.0.0.0', port=3000)