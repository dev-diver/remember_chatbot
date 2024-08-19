from chatbot.prompt import system_role, instruction
from chatbot.chatbot import Chatbot
from interface import ollamaModelNames
from chatbot.config import ASSISTANT_NAME, USER_NAME

chatbot = Chatbot(
    modelName=ollamaModelNames.basic,
    system_role=system_role,
    instruction=instruction,
    user = USER_NAME,
    assistant = ASSISTANT_NAME,
)