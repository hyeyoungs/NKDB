# 1. Mongo의 모든 문서 --> list of document
import pymongo
import urllib.parse

username = urllib.parse.quote_plus('hyeyoung')
password = urllib.parse.quote_plus('mongodb!@wrlove')

MONGO_HOST = "localhost"
MONGO_PORT = "27017"
MONGO_DB = "NKDB"
MONGO_USER = username
MONGO_PASS = password

uri = "mongodb://{}:{}@{}:{}/{}?authSource=admin".format(MONGO_USER, MONGO_PASS, MONGO_HOST, MONGO_PORT, MONGO_DB)
connection = pymongo.MongoClient(uri)


db = connection["NKDB"]
nkdb_collection = db["nkdb"]

def make_doclist(collection):
    doc_list = []
    # nkdb_collection에 있는 document를 가져와 docs에 저장하자.
    docs = collection.find()
    #count = docs.count()
    # docs에 있는 전체 document를 반복해서 접근할텐데
    # 하나의 문서에 접근할 때마다 doc에 저
    for doc in docs:
        if isinstance(doc["post_title"], str) == False:
            continue
        temp_list = doc["post_title"]
        if isinstance(doc["post_body"], str):
            temp_list += doc["post_body"]

        if doc.get("file_extracted_content"):
            file_temp_list = doc["file_name"] + doc["file_extracted_content"]
            temp_list += file_temp_list
        doc_list.append(temp_list)

    print(len(doc_list))
    return doc_list

texts = make_doclist(nkdb_collection)

import pickle
with open('doc_list.txt', 'wb') as f:
    pickle.dump(texts, f)