import time
from flask import Flask, render_template, request

from chatbot import chatbot

application = Flask(__name__)

@application.route('/')
def chat_app():
    return render_template('chat.html')

@application.route('/chat-api', methods=['POST'])
def chat_api():
    start_time = time.time()
    request_message = request.form.get("message", "")
    chatbot.add_user_message(request_message)
    response = chatbot.send_request()

    chatbot.add_response(response)
    response_message = chatbot.get_response_content()
    chatbot.handle_token_limit()
    
    end_time = time.time()
    print("총 시간:", end_time - start_time)
    return {"response_message" : response_message}

@application.route('/make-memory', methods=['POST'])
def make_memory():
    data = request.get_json()
    message = data.get("message", "")
    print("inject memory:", message)
    summaries = chatbot.memoryManager.inject_memory(message)
    return {"message" : summaries}

if __name__ == '__main__':
    print("Starting the application")
    application.run(host='0.0.0.0', port=3000)