from common import models, client
import base64

def ask_image(image_file, jjinchin):
    user_message = jjinchin.context[-1]['content'] + jjinchin.instruction
    prompt = f"절친이 이 이미지에 대해 다음과 같이 말하고 있습니다.:\n{user_message}"
    encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
    return ask_gpt_vision(prompt, encoded_image)

def ask_gpt_vision(prompt, encoded_image):        
    context = [{
        "role": "user",
        "content": [
            {"type": "text",
            "text": prompt},
            {"type": "image_url","image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
        ]}
    ]
    print("gpt-vision 요청")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=context,
        max_tokens=300,
    )
    return response.model_dump()


    
    