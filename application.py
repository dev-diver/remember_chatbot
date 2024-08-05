from flask import Flask, render_template, request

application = Flask(__name__)

@application.route('/')
def hello():
    return "Hello there!"

@application.route('/chat-app')
def chat_app():
    return render_template('chat.html')

@application.route('/chat-api', methods=['POST'])
def chat_api():
    print("request.json:", request.json)
    return {"response_message": "나도" + request.json['request_message']}

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=8080)