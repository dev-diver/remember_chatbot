import os
from typing import Any

from pymongo import MongoClient
from pymongo.database import Database
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore

from common import embeddings

PINECONE_INDEX = "chatbot-eu"
MONGODB_COLLECTION = "memory"

print("connection mongodb..")
cluster : MongoClient[dict[str,Any]] = MongoClient("mongodb://localhost:27017/")
db :Database[Any] = cluster["chatbot"]
mongo_chats_collection = db["chats"]
mongo_memory_collection = db[MONGODB_COLLECTION]

pinecone_api_key = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=pinecone_api_key)
pinecone_index = pc.Index(PINECONE_INDEX) #type: ignore

pinecone_store = PineconeVectorStore(index = pinecone_index, embedding=embeddings)