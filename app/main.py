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
    message = request.form.get("message", "")
    print("inject memory:", message)
    try:
        summaries = chatbot.memoryManager.inject_memory(message)
        summary = summaries[0]['요약']
    except:
        summary = "요약을 할 수 없습니다."
    return {"response_message" : summary}

if __name__ == '__main__':
    print("Starting the application")
    application.run(host='0.0.0.0', port=3000)