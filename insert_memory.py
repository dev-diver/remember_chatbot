from openai import OpenAI
import os
from pymongo import MongoClient
from pinecone.grpc import PineconeGRPC as Pinecone
import json

from common import embedding_to_vector

PINECONE_INDEX = "chatbot-eu"
MONGODB_COLLECTION = "memory"

pinecone_api_key = os.getenv("PINECONE_API_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

pinecone = Pinecone(api_key=pinecone_api_key)
pinecone_index = pinecone.Index(PINECONE_INDEX)

cluster = MongoClient("mongodb://localhost:27017/")
db = cluster["chatbot"]
mongo_memory_collection = db[MONGODB_COLLECTION]

embedding_model = "text-embedding-ada-002"

with open("대화내용요약.json", 'r', encoding='utf-8') as f:
    summaries_list = json.load(f)

mongo_memory_collection.delete_many({})

next_id = 1

for list_idx, summaries in enumerate(summaries_list):
    date = f"202408{list_idx+1:02}"

    for summary in summaries:
        vector = embedding_to_vector(summary["요약"])

        metadata= {"date": date, "keyword": summary["주제"]}
        upsert_response = pinecone_index.upsert([(str(next_id), vector, metadata)])

        query = {"_id": next_id }
        newvalues = {"$set": {"date": date, "keyword": summary["주제"], "summary": summary["요약"]}}
        mongo_memory_collection.update_one(query, newvalues, upsert=True)

        if (next_id) % 5 == 0 :
            print(f"id: {next_id}")

        next_id += 1 