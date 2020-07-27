from gensim.models import word2vec

model = word2vec.Word2Vec.load('/home/hyeyoung/NKDB/model/CBOW_model.model')

input_query = "대통령" # query에 대해 형태소 분석 기능 추가 필요

associate_word = model.wv.most_similar(positive=[input_query])
print(associate_word)
print(associate_word[0])
print()

associate_word2 = model.wv.most_similar(positive=["문재인", "북한"], negative=["남한"], topn=1)
print(associate_word2)
print(associate_word2[0])
print()

print(model.wv.most_similar(positive=['서울', '일본'], negative=['한국']))
print()

print(model.wv.most_similar(positive=['왕', '남자'], negative=['여자']))

print(model.wv.most_similar(positive=["김대중", "북한"], negative=["남한"], topn=1))