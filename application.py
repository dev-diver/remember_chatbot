from flask import Flask, render_template

application = Flask(__name__)

@application.route('/')
def hello():
    return "Hello there!"

@application.route('/chat-app')
def chat_app():
    return render_template('chat.html')

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=8080)