# 1. Mongo의 모든 문서 --> list of document
import pymongo
from pymongo import MongoClient

connection = pymongo.MongoClient('localhost', 27017)
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
        temp_list = doc["post_title"] + doc["post_body"]
        if doc.get("file_extracted_content"):
            file_temp_list = doc["file_name"] + doc["file_extracted_content"]
            temp_list += file_temp_list
            # 리스트에 temp_dict 추가
        doc_list.append(temp_list)

    print(doc_list)
    print("전체 document의 수: ", count)

    return doc_list

    #return count, doc_list

#count, texts = make_doclist(nkdb_collection)
text = make_doclist(nkdb_collection)

# 2. list of document 형태소 분석 적용
from konlpy.tag import Okt
okt=Okt()

morphs_texts = []
for index in range(0, len(texts)):
  morphs_texts.append(okt.morphs(texts[index]))

for index in range(0, len(morphs_texts)):
  morphs_texts[index] = ' '.join(morphs_texts[index])

print(morphs_texts)
print("전체 document의 수: ", len(morphs_texts))

# 3. gensim 사용해 BoW 생성
from gensim.sklearn_api import Text2BowTransformer

# Create a transformer.
model = Text2BowTransformer()

# Use sklearn-style `fit_transform` to get the BOW representation of each document.
BoW = model.fit_transform(morphs_texts)
# print("BoW >> \n", BoW)

# 4. gensim 사용해 Tf-idf 적용
from gensim.models import TfidfModel
model = TfidfModel(BoW) # fit model

for index in range(0, len(BoW)):
  vector = model[BoW[index]]
  print(vector)
