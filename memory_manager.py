from pymongo import MongoClient
import os
from common import today, models, client, yesterday, currTime
from pinecone.grpc import PineconeGRPC as Pinecone
import json


cluster = MongoClient("mongodb://localhost:27017/")
db = cluster["chatbot"]
mongo_chats_collection = db["gobi"]

pinecone_api_key = os.getenv("PINECONE_API_KEY")
pinecone = Pinecone(api_key=pinecone_api_key)
pinecone_index = pinecone.Index("chatbot")

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

class MemoryManager:

    def save_chat(self, context):
        messages = []
        for message in context:
            if message.get("saved", True):
                continue
            messages.append({"date":today(), "role":message["role"], "content":message["content"]})

        if len(messages) > 0 :
            mongo_chats_collection.insert_many(messages)

    def restore_chat(self, date=None):
        search_date = date if date is not None else today()
        search_results = mongo_chats_collection.find({"date":search_date})
        restored_chat = [{"role": v['role'], "content": v['content'], "saved": True} for v in search_results]
        return restored_chat
    
    def needs_memory(self, message):
        context = [{"role":"user", "content": NEEDS_MEMORY_TEMPLATE.format(message=message)}]
        try:
            response = client.chat.completions.create(
                model=models.advanced,
                messages=context,
                temperature=0,
            ).model_dump()
            print("needs_memory", response['choices'][0]['message']['content'])
            return True if response['choices'][0]['message']['content'].upper() == "TRUE" else False
        except Exception as e:
            return False
        
    def search_mongo_db(self, _id):
        search_result = mongo_chats_collection.find_one({"_id": int(_id)})
        print("search_result", search_result)
        return search_result["summary"]
    
    def search_vector_db(self, message):
        query_vector = client.embeddings.create(
            input = message,
            model=embedding_model
        ).data[0].embedding
        results = pinecone_index.query(
            top_k=1,
            vector=query_vector,
            include_metadata=True,
        )
        id, score = results['matches'][0]['id'], results['matches'][0]['score']
        print("id", id, "score", score)
        return id if score > 0.7 else None
    
    def retrieve_memory(self,message):
        vector_id = self.search_vector_db(message)
        if not vector_id:
            return None
        memory = self.search_mongo_db(vector_id)
        if self.filter(message, memory):
            return memory
        else:
            return None
    
    def filter(self, message, memory, threshhold=0.6):
        context = [
            {"role": "system", "content": MEASURING_SIMILARITY_SYSTEM_ROLE},
            {"role": "user", "content": f'{{"statement1": "민지:{message}, "statement2": {memory}}}'}
        ]
        try:
            response = client.chat.completions.create(
                model=models.advanced,
                messages=context,
                temperature=0,
                response_format={"type":"json_object"}
            ).model_dump()
            prob = json.loads(response['choices'][0]['message']['content'])['probability']
            print("filter prob", prob)
        except Exception as e:
            print("filter exception", e)
            prob=0
        return prob >= threshhold

