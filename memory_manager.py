from pymongo import MongoClient
import os
from common import today, models, client, yesterday, currTime
from pinecone.grpc import PineconeGRPC as Pinecone
import json

cluster = MongoClient("mongodb://localhost:27017/")
db = cluster["chatbot"]
mongo_chats_collection = db["chats"]
mongo_memory_collection = db["memory"]

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

    def __init__(self, **kwargs):
        self.user = kwargs["user"]
        self.assistant = kwargs["assistant"]
        
    def search_mongo_db(self, _id):
        search_result = mongo_memory_collection.find_one({"_id": int(_id)})
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
    
    def retrieve_memory(self,message):
        vector_id = self.search_vector_db(message)
        if not vector_id:
            return None
        memory = self.search_mongo_db(vector_id)
        if self.filter(message, memory):
            return memory
        else:
            return None
    
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
    
    def save_chat(self, context):
        messages = []
        for message in context:
            if message.get("saved", True):
                continue
            messages.append({"date":today(), "role":message["role"], "content":message["content"]})

        if len(messages) > 0 :
            mongo_chats_collection.insert_many(messages)
        print("대화 저장 완료: " , messages)

    def restore_chat(self, date=None):
        search_date = date if date is not None else today()
        search_results = mongo_chats_collection.find({"date":search_date})
        restored_chat = [{"role": v['role'], "content": v['content'], "saved": True} for v in search_results]
        return restored_chat
    
    def summarize(self, messages):
        altered_messages = [
            {
                f"{self.user if message['role'] == 'user' else self.assistant}": message['content']
            } for message in messages
        ]
        try:
            context = [
                {"role":"system", "content":SUMMARIZING_TEMPLATE},
                {"role":"user", "content": json.dumps(altered_messages, ensure_ascii=False)}]
            response = client.chat.completions.create(
                model=models.basic,
                messages=context,
                temperature=0,
                response_format={"type":"json_object"}
            ).model_dump()
            return json.loads(response['choices'][0]['message']['content'])['data']
        except Exception as e:
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
        self.delete_by_date(date) #1시간 마다 반복이기 때문에, 중복이 생겨서 추가를 의도. 길이가 길면 실행 안되게는 왜 했는지 모르겠음..
        self.save_to_memory(summaries,date)
        print("기억 저장 완료", summaries)
    
    def delete_by_date(self,date):
        search_results = mongo_memory_collection.find({"date":date})
        ids = [ str(v['_id']) for v in search_results]
        if len(ids) == 0:
            return
        pinecone_index.delete(ids=ids)
        mongo_memory_collection.delete_many({"date":date})

    def save_to_memory(self, summaries, date):
        next_id = self.next_memory_id() #id 일치를 위함
        for summary in summaries:
            vector = client.embeddings.create(
                input = summary['요약'],
                model=embedding_model
            ).data[0].embedding
            metadata = {"date":date, "summary":summary['주제']}
            pinecone_index.upsert([(str(next_id), vector, metadata)])

            query = {"_id":next_id}
            newvalues = {"$set": {"date":date, "keyword": summary['주제'], "summary":summary['요약']}}
            mongo_memory_collection.update_one(query, newvalues, upsert=True)
            next_id += 1
    
    def next_memory_id(self):
        result =  mongo_memory_collection.find_one(sort=[('_id', -1)])
        return 1 if result is None else result['_id'] + 1