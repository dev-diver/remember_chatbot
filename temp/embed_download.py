from transformers import AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer, models
from langchain_huggingface import HuggingFaceEmbeddings

# model_name :str = "skt/kobert-base-v1"
# model_name :str = "./local_kobert"
model_name :str = "bespin-global/klue-sroberta-base-continue-learning-by-mnr"
model_path :str = "./local_klue"

# huggingface에서 모델 로드
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

# 모델 저장
tokenizer.save_pretrained(model_path)
model.save_pretrained(model_path)

# 모델을 SentenceTransformer로 변환
word_embedding_model = models.Transformer(model_name, max_seq_length=256)
pooling_model = models.Pooling(word_embedding_model.get_word_embedding_dimension())
sentence_model = SentenceTransformer(modules=[word_embedding_model, pooling_model])

# sentence 모델 저장
sentence_model.save(model_path)

def embedding_to_vector(model_path:str, input :str):
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    embedding_model = AutoModel.from_pretrained(model_path) #type: ignore
    inputs = tokenizer(input, return_tensors="pt", truncation=True, padding=True)
    inputs.pop("token_type_ids")
    outputs = embedding_model(**inputs) #type: ignore
    print(outputs)
    tensor = outputs.last_hidden_state #type: ignore
    # embedding_vector = tensor[0][0].tolist()
    embedding_vector = tensor.mean(dim=1).squeeze().tolist()
    return embedding_vector

def sentence_embedding_to_vector(model_path:str, input: str):
    model = SentenceTransformer(model_path)
    embeddings = model.encode([input])
    return embeddings[0].tolist()

text = "안녕하세요"
embedding = embedding_to_vector(model_path, text)
# sentence_embedding = sentence_embedding_to_vector(model_path, text)
# print("-"*100, "embedding\n", embedding)
# print("-"*100, "sentence\n" ,sentence_embedding)
# if(embedding == sentence_embedding):
#     print("same")
# else:
#     print("different")