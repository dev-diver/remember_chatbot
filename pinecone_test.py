from openai import OpenAI
import os
from pinecone.grpc import PineconeGRPC as Pinecone
import time

pinecone_api_key = os.getenv("PINECONE_API_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

pc = Pinecone(api_key=pinecone_api_key)
index = pc.Index("chatbot")

text1= """
신데렐라는 어려서 부모를 잃고 불친절한 새어머니와 언니들과 삽니다. 요정 대모님의 마법으로 왕자님의 무도회에 참석합니다. 밤 12시가 되면 마법이 풀린다는 조건 하에 왕자님과 춤을 추고, 서둘러 도망치면서 유리구두 하나를 잃습니다. 왕자님은 유리구두를 가지고 신데렐라를 찾아 결혼하게 됩니다.
"""

text2 =  """
컴퓨터 구조는 CPU, 메모리, 입출력 장치 등으로 구성되며, 이들은 버스로 연결됩니다. CPU는 명령어를 실행하고, 메모리는 데이터와 프로그램을 저장합니다. 입출력 장치는 사용자와 시스템 간의 상호작용을 담당합니다. 이 구성 요소들은 소프트웨어와 하드웨어의 효율적인 동작을 위해 설계되었습니다.
"""

vector1 = client.embeddings.create(input=text1, model="text-embedding-ada-002").data[0].embedding
vector2 = client.embeddings.create(input=text2, model="text-embedding-ada-002").data[0].embedding

index.upsert(
    vectors = [
        {"id": "id1", "values": vector1, "metadata": {"input_date": "20230801"}},
        {"id": "id2", "values": vector2, "metadata": {"input_date": "20230801"}}
    ]
)