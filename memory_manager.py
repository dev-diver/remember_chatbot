from pymongo import MongoClient
from pymongo.database import Database

import os
from common import today, models, client, request_to_llm, ChatbotKwargs
from chatbot import Context

from pinecone.grpc import PineconeGRPC as Pinecone
import json
from typing import Any, Dict
from pymongo.cursor import Cursor

from typing import Dict, Any, Unpack

from pinecone.grpc.index_grpc import GRPCIndex

print("connection mongodb..")
cluster : MongoClient[Dict[str,Any]] = MongoClient("mongodb://localhost:27017/")
db :Database[Any] = cluster["chatbot"]
mongo_chats_collection = db["chats"]
mongo_memory_collection = db["memory"]

pinecone_api_key = os.getenv("PINECONE_API_KEY")
pinecone = Pinecone(api_key=pinecone_api_key)
pinecone_index : GRPCIndex = pinecone.Index("chatbot") #type: ignore

embedding_model = "text-embedding-ada-002"

NEEDS_MEMORY_TEMPLATE = """
Answer only true/false if the user query belows asks about memories before today.
```
{message}
```
"""

MEASURING_SIMILARITY_SYSTEM_ROLE="""
statement1 is a question about memory.
statement2 is a memory shared by '민지' and '고비'.
Answer whether statement2 is apporipriate as a memory for statement1 in the following JSON format
{"probability": <between 0 and 1>}
"""

SUMMARIZING_TEMPLATE = """
당신은 사용자의 메시지를 아래의 JSON 형식으로 대화 내용을 주제별로 요약하는 기계입니다.
1. 주제는 구체적이며 의미가 있는 것이어야 합니다.
2. 요약 내용에는 '민지는...', '고비는...'처럼 대화자의 이름이 들어가야 합니다.
3. 원문을 최대한 유지하며 요약해야 합니다.
4. 주제의 갯수는 무조건 5개를 넘지 말아야 하며 비슷한 내용은 하나로 묶어야 합니다.
```
{
    "data": 
        [
            {"주제":<주제>, "요약":<요약>},
            {"주제":<주제>, "요약":<요약>},
        ]
}
```
"""

class MemoryManager:

    def __init__(self, **kwargs : Unpack[ChatbotKwargs]):
        self.user = kwargs.get("user", "사용자")
        self.assistant = kwargs.get("assistant", "챗봇")
        
    def search_mongo_db(self, _id :str) -> str:
        search_result = mongo_memory_collection.find_one({"_id": int(_id)})
        print("search_result", search_result)

        if search_result is None:
            raise ValueError(f"search_mongo_db: {_id} not found")
        return search_result["summary"]
    
    def search_vector_db(self, message :str) -> str|None:
        query_vector = client.embeddings.create(
            input = message,
            model=embedding_model
        ).data[0].embedding
        results = pinecone_index.query( #type: ignore
            vector=query_vector,
            top_k=1,
            include_metadata=True,
        )
        id, score = results['matches'][0]['id'], results['matches'][0]['score']
        print("id", id, "score", score)
        return id if score > 0.7 else None
    
    def filter(self, message :str, memory :str, threshhold :float=0.6):
        context :list[Context] = [
            {"role": "system", "content": MEASURING_SIMILARITY_SYSTEM_ROLE, "saved": False},
            {"role": "user", "content": f'{{"statement1": "민지:{message}, "statement2": {memory}}}', "saved": False}
        ]
        try:
            response = request_to_llm("ollama", models.advanced, context, temperature=0)

            resp = json.loads(response)
            prob = resp['probablility']
            print("filter prob", prob)
        except Exception as e:
            print("filter exception", e)
            prob=0
        return prob >= threshhold
    
    def retrieve_memory(self, message :str) -> str|None:
        vector_id = self.search_vector_db(message)
        if not vector_id:
            return None
        memory = self.search_mongo_db(vector_id)
        if self.filter(message, memory):
            return memory
        else:
            return None
    
    def needs_memory(self, message:str) -> bool:
        context : list[Context] = [{"role":"user", "content": NEEDS_MEMORY_TEMPLATE.format(message=message), "saved": False}]
        try:
            response = request_to_llm("ollama", models.advanced, context, temperature=0)
            return True if response.upper() == "TRUE" else False
        except Exception:
            return False
    
    def save_chat(self, context : list[Context]):
        messages :list[dict[str,str]] = []
        for message in context:
            if message.get("saved", True):
                continue
            messages.append({"date":today(), "role":message["role"], "content":message["content"]})

        if len(messages) > 0 :
            mongo_chats_collection.insert_many(messages)
        print("대화 저장 완료: " , messages)

    def restore_chat(self, date: str|None=None) -> list[Context]:
        search_date = date if date is not None else today()
        search_results : Cursor[Any] = mongo_chats_collection.find({"date":search_date})
        restored_chat : list[Context] = [{"role": v['role'], "content": v['content'], "saved": True} for v in search_results]
        return restored_chat
    
    def summarize(self, messages : list[Context]) -> list[dict[str,str]]:
        altered_messages = [
            {
                f"{self.user if message['role'] == 'user' else self.assistant}": message['content']
            } for message in messages
        ]
        try:
            context : list[Context] = [
                {"role":"system", "content":SUMMARIZING_TEMPLATE, "saved": False},
                {"role":"user", "content": json.dumps(altered_messages, ensure_ascii=False), "saved": False}
            ]
            response = request_to_llm(
                "ollama", 
                models.advanced, 
                context, 
                temperature=0,
                format="json"
            )
            return json.loads(response)['data']
        except Exception:
            return []

    def build_memory(self):
        date = today()
        memory_results = mongo_memory_collection.find({"date":date})
        if len(list(memory_results)) > 0 :
            return
        chats_results = self.restore_chat(date)
        if len(list(chats_results)) == 0:
            return
        summaries = self.summarize(chats_results)
        self.delete_by_date(date) 
        self.save_to_memory(summaries,date)
        print("기억 저장 완료", summaries)
    
    def delete_by_date(self,date :str):
        search_results = mongo_memory_collection.find({"date":date})
        ids = [ str(v['_id']) for v in search_results]
        if len(ids) == 0:
            return
        pinecone_index.delete( #type: ignore
            ids=ids
        )
        mongo_memory_collection.delete_many({"date":date})

    def save_to_memory(self, summaries: list[dict[str, str]], date: str):
        next_id = self.next_memory_id() #id 일치를 위함
        for summary in summaries:
            vector = client.embeddings.create(
                input = summary['요약'],
                model=embedding_model
            ).data[0].embedding
            metadata = {"date":date, "summary":summary['주제']}
            pinecone_index.upsert( #type: ignore
                [(str(next_id), vector, metadata)]
            )

            query = {"_id":next_id}
            newvalues = {"$set": {"date":date, "keyword": summary['주제'], "summary":summary['요약']}}
            mongo_memory_collection.update_one(query, newvalues, upsert=True)
            next_id += 1
    
    def next_memory_id(self):
        result =  mongo_memory_collection.find_one(sort=[('_id', -1)])
        return 1 if result is None else result['_id'] + 1