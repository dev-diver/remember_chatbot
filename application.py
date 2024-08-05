from flask import Flask, render_template, request
from characters import system_role, instruction
from chatbot import Chatbot
from common import models
from function_calling import FunctionCalling, tools

jjinchin = Chatbot(
    modelName=models.basic,
    # modelName=models.advanced,
    system_role=system_role,
    instruction=instruction
)

func_calling = FunctionCalling(models.basic, jjinchin)

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

    analyzed, analyzed_dict = func_calling.analyze(request_message, tools)
    if analyzed_dict.get("tool_calls"):
        response = func_calling.run(analyzed,analyzed_dict)
        jjinchin.add_response(response)
    else:
        response = jjinchin.send_request()
        jjinchin.add_response(response)

    response_message = jjinchin.get_response_content()
    jjinchin.handle_token_limit()
    
    print("response_message:", response_message)
    return {"response_message": response_message}

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=8080)