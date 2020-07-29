#-*- coding: utf-8 -*-

import pickle
with open('result_list.txt', 'rb') as f:
    data = pickle.load(f)

import pymongo

uri = "mongodb://localhost:27017"
connection = pymongo.MongoClient(uri)

db = connection["NKDB_morphs"]
nkdb_collection = db["nkdb"]
