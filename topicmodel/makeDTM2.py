import pickle
with open('/home/hyeyoung/NKDB/data/corpus.txt', 'rb') as f:
    corpus = pickle.load(f) # 단 한줄씩 읽어옴

from gensim import models
# 4. 만들어진 사전 정보를 가지고 벡터화 하기
tfidf = models.TfidfModel(corpus)
corpus_tfidf = tfidf[corpus]

print(tfidf)
#print(corpus_tfidf)

with open('/home/hyeyoung/NKDB/data/corpus_tfidf.txt', 'wb') as f:
    pickle.dump(corpus_tfidf, f)