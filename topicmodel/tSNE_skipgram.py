#-*- coding: utf-8 -*-


from gensim.models import Word2Vec
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import pandas as pd

model = Word2Vec.load("/home/hyeyoung/NKDB/model/Skipgram_model.model")
vocab = model.wv.vocab
X = model[vocab]

tsne = TSNE(n_components=2)

X_tsne = tsne.fit_transform(X[:100,:])
df = pd.DataFrame(X_tsne, index=vocab[:100], columns=['x', 'y'])
df.head(10)



fig = plt.figure()
fig.set_size_inches(40,20)
ax = fig.add_subplot(1, 1, 1)

ax.scatter(df['x'], df['y'])

for word, pos in df.iterrows():
    ax.annotate(word, pos, fontsize=30)
plt.show()