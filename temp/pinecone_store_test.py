import os
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document

from langchain_huggingface import HuggingFaceEmbeddings

PINECONE_INDEX = "chatbot-eu"
MONGODB_COLLECTION = "memory"

pinecone_api_key = os.getenv("PINECONE_API_KEY")

pc = Pinecone(api_key=pinecone_api_key)
pinecone_index = pc.Index(PINECONE_INDEX) #type: ignore

model_name :str = "bespin-global/klue-sroberta-base-continue-learning-by-mnr"
embeddings = HuggingFaceEmbeddings(model_name=model_name)
vector_store = PineconeVectorStore(index = pinecone_index, embedding=embeddings)

metadata= {"keyword": "요약"}
document = Document(
    page_content="안녕하세요",
    metadata=metadata
)

print(document)
# vector_store.add_documents(
#     documents=[document], 
#     ids=["1"]
# )

results = vector_store.similarity_search_with_score(
    query="안녕하세요",
    k=1
)

print(results)