from flask import Flask, render_template, request, Response, url_for
import sys
from common import models
from chatbot import Chatbot
from characters import system_role, instruction
import multimodal

# jjinchin 인스턴스 생성
jjinchin = Chatbot(
    modelName = models.basic,
    system_role = system_role,
    instruction = instruction,
    user = "민지",
    assistant = "고비",
)

application = Flask(__name__)

@application.route("/chat-app")
def chat_app():
    return render_template("chat.html")

@application.route('/chat-api', methods=['POST'])
def chat_api():       
    request_message = request.form.get("message")
    print("request_message:", request_message)
    jjinchin.add_user_message(request_message)
    
    response_image = None
    image_file = request.files.get('image')
    if image_file is not None:
        response = multimodal.ask_image(image_file, jjinchin)
    elif multimodal.is_drawing_request(request_message):    
        encoded_image, response = multimodal.create_image(jjinchin)
        if encoded_image:
            response_image = f"data:image/png;base64,{encoded_image}"                            
    else:
        response = jjinchin.send_request()        
            
    jjinchin.add_response(response)        
    response_message = jjinchin.get_response_content()         
    jjinchin.handle_token_limit()
    print("response_message:", response_message)
    return {"response_message" : response_message, "image": response_image}
 
if __name__ == "__main__":  
    application.run(host="0.0.0.0", port=3000)