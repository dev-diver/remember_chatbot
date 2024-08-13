from transformers import AutoTokenizer, AutoModel

# model_name :str = "skt/kobert-base-v1"
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# model = AutoModel.from_pretrained(model_name)

# # 로컬 디렉토리에 저장
# tokenizer.save_pretrained("./local_kobert")
# model.save_pretrained("./local_kobert")

tokenizer = AutoTokenizer.from_pretrained("./local_kobert")
embedding_model = AutoModel.from_pretrained("./local_kobert") #type: ignore

def embedding_to_vector(input :str):
    inputs = tokenizer(input, return_tensors="pt", truncation=True, padding=True)
    inputs.pop("token_type_ids")
    outputs = embedding_model(**inputs) #type: ignore
    tensor = outputs.last_hidden_state #type: ignore
    embedding_vector = tensor[0][0].tolist()
    # torch.mean(embeddings, dim=1).squeeze().tolist()
    print("embedding_vector:", embedding_vector)
    
    return embedding_vector

embedding_to_vector("안녕하세요")