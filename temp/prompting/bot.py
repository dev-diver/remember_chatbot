import time
from langchain_ollama import ChatOllama
from typing import TypedDict, Optional, Literal, cast, Dict, Any
from typing_extensions import Unpack

from langchain_core.messages.base import BaseMessage
from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage
import json

model_name = "EEVE:latest"
sys_message = None

class LLMOptions(TypedDict, total=False):
    temperature: Optional[float]
    top_p: Optional[float]
    max_tokens: Optional[int]
    frequency_penalty: Optional[float]
    format: Optional[str]

def request_to_llm(message:str, sys_message:str="", **kwargs : Unpack[LLMOptions]) -> str | Dict[str,Any] | None:
    format_value = cast(Literal['', 'json'], kwargs.get("format", ''))
    model = ChatOllama(
        model = model_name,
        temperature = kwargs.get("temperature", None),
        top_p = kwargs.get("top_p", None),
        num_predict = kwargs.get("max_tokens", None),
        repeat_penalty = kwargs.get("frequency_penalty", None),
        format = format_value
        #Presence penalty 없음
    )
    prompt_context :list[BaseMessage]= []
    if sys_message!="":
        sys_context = SystemMessage(content=sys_message)
        prompt_context.append(sys_context)
    prompt_context.append(HumanMessage(content=message))
    print("request: ", prompt_context)
    print("요청중..")
    start_time = time.time()
    response = model.invoke(prompt_context)
    end_time = time.time()
    content = getattr(response, "content", "")

    if(format_value == "json"):
        try:
            json_content :Dict[str, Any] = json.loads(content)
            print("response: ", json_content)
            print("Elapsed time: ", end_time - start_time)
            return json_content
        except Exception as e:
            print("JSON parsing error: ", e)
            print("Elapsed time: ", end_time - start_time)
            return None
    
    usage_metadata = getattr(response, "usage_metadata", {})
    input_tokens = usage_metadata.get("input_tokens", 0)
    output_tokens = usage_metadata.get("output_tokens", 0)

    print("response: ", content)    
    print("Elapsed time: ", end_time - start_time)
    print("input_tokens: ", input_tokens, " output_tokens:", output_tokens)
    return content