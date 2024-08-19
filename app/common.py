from typing import Literal, cast
from typing_extensions import Unpack

import os
import time
import warnings
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from langchain_core.messages.base import BaseMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_ollama import ChatOllama

from langchain_huggingface import HuggingFaceEmbeddings

from interface import LLMOptions, Context

warnings.filterwarnings("ignore", category=FutureWarning)

os.environ["LANGCHAIN_TRACING_V2"] = "true"
model_name :str = "bespin-global/klue-sroberta-base-continue-learning-by-mnr"
embeddings = HuggingFaceEmbeddings(model_name=model_name)

def request_to_llm(platform :str, modelName :str, context :list[Context], **kwargs : Unpack[LLMOptions]) -> str:
    model : BaseChatModel | None = None
    format_value = cast(Literal['', 'json'], kwargs.get("format", ''))
    if platform == "ollama":
        model = ChatOllama(
            model = modelName,
            temperature = kwargs.get("temperature", None),
            top_p = kwargs.get("top_p", None),
            num_predict = kwargs.get("max_tokens", None),
            repeat_penalty = kwargs.get("frequency_penalty", None),
            format = format_value
        )

    if model is None:
        raise ValueError(f"Unknown platform: {platform}")
    prompt_context = context_to_messages(context)
    print("prompt_context:", prompt_context)
    print("요청중..")
    start_time = time.time()
    response = model.invoke(prompt_context)
    end_time = time.time()
    print("Elapsed time:", end_time - start_time)
    print("응답:", response)
    usage_metadata = getattr(response, "usage_metadata", {})
    input_tokens = getattr(usage_metadata,"input_tokens", 0)
    output_tokens = getattr(usage_metadata,"output_tokens", 0)
    print("input_tokens:", input_tokens, " output_tokens:", output_tokens)
    content = getattr(response, "content", "")
    return content

def context_to_messages(context: list[Context]) -> list[BaseMessage]:
    invokeMessages:list[BaseMessage] = []
    for message in context:
        if(message["role"] == "system"):
            invokeMessages.append(SystemMessage(content=message["content"]))
        elif(message["role"] == "user"):
            invokeMessages.append(HumanMessage(content=message["content"]))
        elif(message["role"] == "assistant"):
            invokeMessages.append(AIMessage(content=message["content"]))
    return invokeMessages

def today() -> str:
    korea = ZoneInfo('Asia/Seoul')
    now = datetime.now(korea)
    return(now.strftime("%Y%m%d"))

def yesterday() -> str:
    korea = ZoneInfo('Asia/Seoul')
    now = datetime.now(korea)
    one_day = timedelta(days=1)
    yesterday = now - one_day
    return(yesterday.strftime("%Y%m%d"))

def currTime() -> str:
    korea = ZoneInfo('Asia/Seoul')
    now = datetime.now(korea)
    formatted_now = now.strftime("%Y.%m.%d %H:%M:%S")
    return(formatted_now)