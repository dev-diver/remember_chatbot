from pymongo import MongoClient

cluster = MongoClient("mongodb://localhost:27017/")
db = cluster["chatbot"]
collection = db["gobi"]

my_friend = {
    "name": "민지",
    "age": 25,
    "city": "서울"
}

collection.insert_one(my_friend)

for result in collection.find({}):
    print(result)