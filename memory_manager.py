from pymongo import MongoClient
from pymongo.database import Database

import os
from common import today, ollamaModelNames, request_to_llm, ChatbotKwargs, embeddings
from memory_prompt import MEASURING_SIMILARITY_SYSTEM_ROLE, NEEDS_MEMORY_TEMPLATE, SUMMARIZING_TEMPLATE
from chatbot import Context

from pinecone import Pinecone
import json
from typing import Any, Dict, List
from pymongo.cursor import Cursor

from typing import Dict, Any, Unpack

from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document

PINECONE_INDEX = "chatbot-eu"
MONGODB_COLLECTION = "memory"

print("connection mongodb..")
cluster : MongoClient[Dict[str,Any]] = MongoClient("mongodb://localhost:27017/")
db :Database[Any] = cluster["chatbot"]
mongo_chats_collection = db["chats"]
mongo_memory_collection = db[MONGODB_COLLECTION]

pinecone_api_key = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=pinecone_api_key)
pinecone_index = pc.Index(PINECONE_INDEX) #type: ignore
class MemoryManager:

    def __init__(self, **kwargs : Unpack[ChatbotKwargs]):
        self.user = kwargs.get("user", "사용자")
        self.assistant = kwargs.get("assistant", "챗봇")
        self.vector_store = PineconeVectorStore(index = pinecone_index, embedding=embeddings)
        
    def search_vector_db(self, message :str) -> str|None:
        results = self.vector_store.similarity_search_with_score( # type: ignore
            message,
            k=1
        )
        # cos_threshold = 0.7
        dist_threshold = 1
        res, score = results[0]
        print("search_vector_db", res, score)
        return res.page_content if score < dist_threshold else None
    
    def filter(self, message :str, memory :str, threshhold :float=0.6):
        context :list[Context] = [
            {"role": "system", "content": MEASURING_SIMILARITY_SYSTEM_ROLE, "saved": False},
            {"role": "user", "content": f'{{"statement1": "민지:{message}, "statement2": {memory}}}', "saved": False}
        ]
        try:
            response = request_to_llm(
                "ollama", 
                ollamaModelNames.advanced, 
                context, 
                temperature=0,
                format="json"
            )

            resp = json.loads(response)
            prob = resp['probability']
            print("filter prob", prob)
        except Exception as e:
            print("filter exception", e)
            prob=0
        return prob >= threshhold
    
    def retrieve_memory(self, message :str) -> str|None:
        print("기억 검색중", message)
        memory = self.search_vector_db(message)
        if memory is None:
            return None #기억 없음
        if self.filter(message, memory):
            return memory
        else:
            return None
    
    def needs_memory(self, message:str) -> bool:
        print("기억 검색이 필요한지 검사중")
        context : list[Context] = [{"role":"user", "content": NEEDS_MEMORY_TEMPLATE.format(message=message), "saved": False}]
        try:
            response = request_to_llm(
                "ollama", 
                ollamaModelNames.advanced, 
                context, 
                temperature=0,
                format="json"
            )
            response = json.loads(response)
            print("기억 필요", response)
            return response['needs_memory']
        except Exception as e:
            print("needs_memory exception", e)
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
                ollamaModelNames.advanced, 
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
    
    def delete_by_date(self, date :str):
        search_results = mongo_memory_collection.find({"date":date})
        ids : List[str] = [ str(v['_id']) for v in search_results]
        if len(ids) == 0:
            return
        self.vector_store.delete(ids=ids) #type: ignore
        mongo_memory_collection.delete_many({"date":date})

    def save_to_memory(self, summaries: list[dict[str, str]], date: str):
        next_id = self.next_memory_id() #id 일치를 위함
        for summary in summaries:
            document = Document(
                page_content=summary['요약'],
                metadata={"date":date, "summary":summary['주제']}
            )
            self.vector_store.add_documents(documents=[document], ids=[str(next_id)])
            
            query = {"_id":next_id}
            newvalues = {"$set": {"date":date, "keyword": summary['주제'], "summary":summary['요약']}}
            mongo_memory_collection.update_one(query, newvalues, upsert=True)
            next_id += 1
    
    def next_memory_id(self):
        result =  mongo_memory_collection.find_one(sort=[('_id', -1)])
        return 1 if result is None else result['_id'] + 1