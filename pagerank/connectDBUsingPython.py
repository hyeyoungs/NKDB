import pymongo
from pymongo import MongoClient

# 1.python으로 mongodatabase 접속하기
connection = pymongo.MongoClient('mongodb://localhost:27017')
# database 객체 할당받기 (해당 데이터베이스의 이름을 문자열로 받는다. --> db = connection["DB_이름"] )
db = connection["nkdb"]
# colleciton 객체 할당받기 (할당받은 db에서 콜렉션 이름을 통해 콜렉션 객체를 할당 받는다. nkdb_collection = db["coll_이름"])
nkdb_collection = db["nkdb"]

# 2. collection에 있는 document 가져오고 싶을 때,
docs = nkdb_collection.find()
# 그러면 docs에
# nkdb collection에 있는 document들이 다 저장되어 있다.

# 3. 각 문서의 post_title 접근해 출력해주고 싶을 때
# docs에 있는 전체 document를 반복해서 접근할텐데
# 하나의 문서에 접근할 때마다 doc에 저장
for doc in docs:
    title = doc["post_title"]
    print(title)

# 2, 3번 개념을 가지고 list of document를 만들어보자
# 만약 우리가 만들고자 하는 list of document는
# [
# {'title': doc["post_title"], 'text': 'doc["post_body"]' (파일이 있다면) + doc[file_extracted_content]},
# {'title': doc["post_title"], 'text': 'doc["post_body"]' (파일이 있다면) + doc[file_extracted_content]},
# {'title': doc["post_title"], 'text': 'doc["post_body"]' (파일이 있다면) + doc[file_extracted_content]}
# ]
# 라고 가정 하면 (이 구조 외에도 다양히 만들 수 있다)

def make_structure(nkdb_collection):
    count = 0
    structure_list = []
    # nkdb_collection에 있는 document를 가져와 docs에 저장하자.
    docs = nkdb_collection.find()
    # docs에 있는 전체 document를 반복해서 접근할텐데
    # 하나의 문서에 접근할 때마다 doc에 저장
    for doc in docs:
        # key값
        keys = ['title', 'text']
        # 문서의 제목에 접근하고 싶으면 doc["post_title"]써주면 된다.
        temp_dict = dict(zip(keys, [doc["post_title"], doc["post_body"]]))
        if doc.get("file_extracted_content"):
            temp_dict["text"] += doc["file_extracted_content"]
        # 리스트에 temp_dict 추가
        structure_list.append(temp_dict)
        count += 1
    print("전체 document의 수: ", count)
    print(structure_list)
    return count, structure_list

make_structure(nkdb_collection)
