#-*- coding: utf-8 -*-

import pickle
with open('/home/hyeyoung/NKDB/data/total_morphs_list.txt', 'rb') as f:
    total_morphs_list = pickle.load(f) # 단 한줄씩 읽어옴

from gensim.corpora.dictionary import Dictionary

dictionary = Dictionary(total_morphs_list)
dictionary.save('nkdb.dict')
corpus = [dictionary.doc2bow(dic) for dic in total_morphs_list]

with open('/home/hyeyoung/NKDB/data/corpus.txt', 'wb') as f:
    pickle.dump(corpus, f)