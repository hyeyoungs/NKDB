from flask import Flask, render_template, request
import json
import search
import re

app = Flask(__name__)

INDEX = search.INDEX


@app.route('/')
def index():
    index_total = search.totalCount(INDEX)
    return render_template('index.html', index_total=index_total)

@app.route('/result', methods=['POST'])
def result():
    total = 10
    temp_query = request.form['keyword']
    corpus = search.elasticsearchGetDocs(total, temp_query)
    return render_template('result.html', docs=corpus)

@app.route('/content/<docID>', methods=['GET'])
def content(docID):
    result_list = search.es.get(index=INDEX, id=docID)['_source']
    ### for contracted url ###
    url_list = re.findall("((http(s)?:\/\/)([a-z0-9\w]+\.*)+[a-z0-9]{2,4})", result_list['published_institution_url'])
    contracted_url = url_list[0][0]
    ###
    if isinstance(result_list['post_body'], str):
        result_list['post_body'] = result_list['post_body'].strip()
    if result_list['post_body'] is None:
        del result_list['post_body']
    #return render_template('content.html', doc=result_list)

    ### for contracted url ###
    return render_template('content.html', doc=result_list, contracted_url = contracted_url)
    ###
if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5000, debug=True)
