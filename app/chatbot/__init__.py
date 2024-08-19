from app.chatbot.prompt import system_role, instruction
from app.chatbot.chatbot import Chatbot
from app.interface import ollamaModelNames

USER_NAME = "소경현" 
ASSISTANT_NAME = "웰리"

chatbot = Chatbot(
    modelName=ollamaModelNames.basic,
    system_role=system_role,
    instruction=instruction,
    user = USER_NAME,
    assistant = ASSISTANT_NAME,
)