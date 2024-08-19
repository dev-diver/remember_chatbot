from flask import Flask, render_template, request
from app.chatbot.prompt import system_role, instruction
from app.chatbot.chatbot import Chatbot
from app.interface import ollamaModelNames
import time

jjinchin = Chatbot(
    modelName=ollamaModelNames.basic,
    system_role=system_role,
    instruction=instruction,
    user = "민지",
    assistant = "고비",
)

application = Flask(__name__)

@application.route('/')
def chat_app():
    return render_template('chat.html')

@application.route('/chat-api', methods=['POST'])
def chat_api():
    start_time = time.time()
    request_message = request.form.get("message", "")
    jjinchin.add_user_message(request_message)
    response = jjinchin.send_request()

    jjinchin.add_response(response)
    response_message = jjinchin.get_response_content()
    jjinchin.handle_token_limit()
    
    end_time = time.time()
    print("총 시간:", end_time - start_time)
    return {"response_message" : response_message}

if __name__ == '__main__':
    print("Starting the application")
    application.run(host='0.0.0.0', port=3000)