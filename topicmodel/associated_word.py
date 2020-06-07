# word2vec 모델 학습
from gensim.models import word2vec

data = word2vec.Text8Corpus('sample_data/kowiki-latest-abstract.xml')
model = word2vec.Word2Vec(data, size = 100, min_count=2, sg=2)
# 100차원 벡터,
# 출현 빈도는 2개 미만은 제외
# 분석 방법론은 Skip-Gram을 선택
model.save("model/wiki_model.model")

# 모델 생성 후 모델을 활용해 동의어 가져오기
model = word2vec.Word2Vec.load('model/wiki_model.model')

input_query = "대통령" # query에 대해 형태소 분석 기능 추가 필요

associate_word = model.most_similar(positive=[input_query])
print(associate_word)
print(associate_word[0])
print()

associate_word2 = model.most_similar(positive=["문재인", "북한"], negative=["남한"], topn=1)
print(associate_word2)
print(associate_word2[0])
print()

print(model.most_similar(positive=['서울', '일본'], negative=['한국']))
print()

print(model.most_similar(positive=['왕', '남자'], negative=['여자']))
