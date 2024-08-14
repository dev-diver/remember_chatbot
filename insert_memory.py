import os
from pinecone import Pinecone
import json

from common import embeddings

from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document

PINECONE_INDEX = "chatbot-eu"
MONGODB_COLLECTION = "memory"

pinecone_api_key = os.getenv("PINECONE_API_KEY")

pc = Pinecone(api_key=pinecone_api_key)
pinecone_index = pc.Index(PINECONE_INDEX) #type: ignore

vector_store = PineconeVectorStore(index = pinecone_index, embedding=embeddings)

with open("대화내용요약.json", 'r', encoding='utf-8') as f:
    summaries_list = json.load(f)

next_id = 1

for list_idx, summaries in enumerate(summaries_list):
    date = f"202408{list_idx+1:02}"

    for summary in summaries:
        metadata= {"date": date, "keyword": summary["주제"]}
        document = Document(
            page_content=summary['요약'],
            metadata=metadata
        )

        print(document, str(next_id))
        vector_store.add_documents(
            documents=[document], 
            ids=[str(next_id)]
        )

        if (next_id) % 5 == 0 :
            print(f"id: {next_id}")

        next_id += 1 