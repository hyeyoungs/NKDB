import pymongo
from pymongo import MongoClient
import scipy
from scipy.sparse import csr_matrix

connection = pymongo.MongoClient('mongodb://localhost:27017')
db = connection["nkdb"]
nkdb_collection = db["nkdb"]

def make_structure(nkdb_collection):
    count = 0
    structure_dict = {}
    docs = nkdb_collection.find()
    for doc in docs:
        keys = ['title', 'text', '_id']
        temp_dict = dict(zip(keys, [doc["post_title"], doc["post_body"], doc["_id"]]))
        print(temp_dict["title"])
        if doc.get("file_extracted_content"):
            temp_dict["text"] += doc["file_extracted_content"]
        structure_dict.update({count : temp_dict})
        count += 1
    print("전체 document의 수: ", count)
    return count, structure_dict

def make_matrix(structure_dict, count):
    rows = list()
    cols = list()
    data = list()
    for i in range(0, count):
        for j in range(0, count):
            if i == j :
                continue
            else:
                if str(structure_dict[j]["text"]).find(str(structure_dict[i]["title"])) != -1:
                    cols.append(i)
                    rows.append(j)
                    data.append(1)
    ranking_matrix = csr_matrix((data, (rows, cols)))
    #print(ranking_matrix)
    return ranking_matrix

count, structure_dict = make_structure(nkdb_collection)
matrix= make_matrix(structure_dict, count)
print(matrix)
