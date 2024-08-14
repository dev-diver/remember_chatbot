from flask import Flask, render_template, request#, Response, url_for
from characters import system_role, instruction
from chatbot import Chatbot
from common import OllamaModels
# from function_calling import FunctionCalling
# import multimodal
# import atexit
import time

jjinchin = Chatbot(
    modelName=OllamaModels.basic,
    # modelName=models.advanced,
    system_role=system_role,
    instruction=instruction,
    user = "민지",
    assistant = "고비",
)

# func_calling = FunctionCalling(models.basic, jjinchin)

application = Flask(__name__)

@application.route('/')
def chat_app():
    return render_template('chat.html')

@application.route('/chat-api', methods=['POST'])
def chat_api():
    start_time = time.time()
    request_message = request.form.get("message", "")
    print("request_message:", request_message)
    jjinchin.add_user_message(request_message)
    # response_image = None
    # image_file = request.files.get('image')
    # if image_file is not None:
    #     response = multimodal.ask_image(image_file, jjinchin)
    # elif multimodal.is_drawing_request(request_message):    
    #     encoded_image, response = multimodal.create_image(jjinchin)
    #     if encoded_image:
    #         response_image = f"data:image/png;base64,{encoded_image}"  
    # else:
    #     response = jjinchin.send_request()
    response = jjinchin.send_request()

    jjinchin.add_response(response)
    response_message = jjinchin.get_response_content()
    jjinchin.handle_token_limit()

    # response_audio = None    
    # if response_image is not None:    
    #     response_audio = url_for('audio_route', message=response_message, _external=True) 
    
    print("response_message:", response_message)
    end_time = time.time()
    print("총 시간:", end_time - start_time)
    return {"response_message" : response_message}
    # return {"response_message" : response_message, "image": response_image, "audio": response_audio}

# @application.route('/audio')
# def audio_route():
#     user_message = request.args.get('message', '')
#     # TTS 요청
#     speech = multimodal.generate_speech(user_message)
#     return Response(speech, mimetype='audio/mpeg')

# @atexit.register
# def shutdown():
#     print("Shutting down...")
#     jjinchin.save_chat()

if __name__ == '__main__':
    print("Starting the application")
    application.run(host='0.0.0.0', port=3000)