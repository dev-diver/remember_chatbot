from openai import OpenAI
import os
from pymongo import MongoClient
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone.grpc.index_grpc import GRPCIndex
import json

from common import embedding_to_vector

PINECONE_EU_INDEX : str = "chatbot-eu"
PINECONE_COS_INDEX : str = "chatbot-cosine"
MONGODB_COLLECTION : str = "memory"

pinecone_api_key = os.getenv("PINECONE_API_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

pinecone = Pinecone(api_key=pinecone_api_key)
pinecone_eu_index : GRPCIndex = pinecone.Index(PINECONE_EU_INDEX, "") #type: ignore
pinecone_cos_index : GRPCIndex = pinecone.Index(PINECONE_COS_INDEX, "") #type: ignore

# cluster = MongoClient("mongodb://localhost:27017/")
# db = cluster["chatbot"]
# mongo_memory_collection = db[MONGODB_COLLECTION]

def save_memory():
    with open("대화내용요약.json", 'r', encoding='utf-8') as f:
        summaries_list = json.load(f)

    mongo_memory_collection.delete_many({})

    next_id = 1

    for list_idx, summaries in enumerate(summaries_list):
        date = f"202408{list_idx+1:02}"

        for summary in summaries:
            vector = embedding_to_vector(summary["요약"])

            metadata= {"date": date, "keyword": summary["주제"]}
            pinecone_eu_index.upsert([(str(next_id), vector, metadata)])
            pinecone_cos_index.upsert([(str(next_id), vector, metadata)])

            query = {"_id": next_id }
            newvalues = {"$set": {"date": date, "keyword": summary["주제"], "summary": summary["요약"]}}
            mongo_memory_collection.update_one(query, newvalues, upsert=True)

            if (next_id) % 5 == 0 :
                print(f"id: {next_id}")

            next_id += 1

def search_vector_db(message :str, index: GRPCIndex) -> str|None:
    query_vector = embedding_to_vector(message)
    results = index.query( #type: ignore
        vector=query_vector,
        top_k=50,
        include_metadata=True,
    )
    for result in results['matches']:
        print(result["id"], result["score"], result["metadata"]["keyword"])


message = input("Press Enter to continue...:")
print("Euclidean"+ "-"*10)
search_vector_db(message, pinecone_eu_index)
print("Cosine"+ "-"*10)
search_vector_db(message, pinecone_cos_index)
