import os
from openai import OpenAI
from langchain_ollama import ChatOllama
from dataclasses import dataclass
import pytz
from datetime import datetime, timedelta
from langchain_core.messages.base import BaseMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

from typing import TypedDict, Optional, Literal, cast
from typing_extensions import Unpack
import time

from transformers import AutoTokenizer, AutoModel

os.environ["LANGCHAIN_TRACING_V2"] = "true"

tokenizer = AutoTokenizer.from_pretrained("./local_kobert")
embedding_model = AutoModel.from_pretrained("./local_kobert") #type: ignore

class ChatbotKwargs(TypedDict, total=False):
    user: str
    assistant: str

@dataclass(frozen=True)
class GPTModels:
    basic: str = "gpt-3.5-turbo-1106"
    advanced: str = "gpt-4-1106-preview"
    vision: str = "gpt-4o"

class OllamaModels:
    basic: str = "EEVE:latest"
    advanced: str = "EEVE:latest"

models = GPTModels()
ollamaModelNames = OllamaModels()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=30, max_retries=1)

class LLMOptions(TypedDict, total=False):
    temperature: Optional[float]
    top_p: Optional[float]
    max_tokens: Optional[int]
    frequency_penalty: Optional[float]
    format: Optional[str]

class Context(TypedDict):
    role: Literal["user", "assistant", "system"]
    content: str
    saved: Optional[bool]

def embedding_to_vector(input :str) -> list[float]:
    inputs = tokenizer(input, return_tensors="pt", truncation=True, padding=True)
    inputs.pop("token_type_ids")
    outputs = embedding_model(**inputs) #type: ignore
    tensor = outputs.last_hidden_state #type: ignore
    embedding_vector : list[float] = tensor[0][0].tolist()
    # embedding_vector += [0.0] * (1536 - len(embedding_vector))
    # torch.mean(embeddings, dim=1).squeeze().tolist()
    # print("embedding_vector:", embedding_vector)
    return embedding_vector

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
            #Presence penalty 없음
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
    response_metadata = getattr(response, "response_metadata", {})
    usage_metadata = getattr(response_metadata, "usage_metadata", {})
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
    korea = pytz.timezone('Asia/Seoul')
    now = datetime.now(korea)
    return(now.strftime("%Y%m%d"))

def yesterday() -> str:
    korea = pytz.timezone('Asia/Seoul')
    now = datetime.now(korea)
    one_day = timedelta(days=1)
    yesterday = now - one_day
    return(yesterday.strftime("%Y%m%d"))

def currTime() -> str:
    korea = pytz.timezone('Asia/Seoul')
    now = datetime.now(korea)
    formatted_now = now.strftime("%Y.%m.%d %H:%M:%S")
    return(formatted_now)