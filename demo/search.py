from elasticsearch import Elasticsearch
import hlight

### Url address of Elasticsearch
localUrl = "http://localhost:9200"
#serverUrl = "http://203.252.117.201:9200"
INDEX = "nkdb200609"

### Elasticsearch Connection
#es = Elasticsearch(serverUrl)
es = Elasticsearch(localUrl)


### make query to transmit to elasticsearch
### input: size, temp_query(= user input query)
### output: es query body(object)
def transmitQuery(size, temp_query):
    doc = {}
    doc['size'] = size

    doc['query'] = {
        "query_string":{
            "fields": ["post_title", "post_body", "file_name", "file_extracted_content", "published_institution"],
            "query": temp_query
        }
    }

    return doc

### count indexed documents in elasticsearch
### input: index name
### output: num of indexed documents in elasticsearch
def totalCount(index_name):
    count_list = es.cat.count(index=index_name, params={"format": "json"})
    count = count_list[0]['count']
    return count

### count num of documents according to query body
### input: es query body
### output: num of documents(int)
def elasticsearchCount(doc):
    count = es.count(index=INDEX, body=doc)
    count = count['count']
    return count

### return data
### input: es query body
### output: json format data (object)
def elasticsearchQuery(doc):
    data = es.search(index=INDEX, body=doc)
    return data

### return documents
### input: count of document to return (int)
### output: document (object array)
def nkdbContent(SIZE, temp_query):
    doc = transmitQuery(SIZE, temp_query)
    temp_result = elasticsearchQuery(doc)

    result = temp_result["hits"]["hits"]
    #num = len(result)
    #print("Number of documents received : ", num)

    corpus = []

    for oneDoc in result:
        if  oneDoc['_source'].get('file_name'):
            hlight_content = hlight.hlight_term(oneDoc['_source']['file_extracted_content'], temp_query)
            try:
                corpus.append(
                                {
                                    "_id" : oneDoc["_id"],
                                    "post_title" : oneDoc["_source"]["post_title"],
                                    "content" : oneDoc["_source"]["file_extracted_content"],
                                    "file_name" : oneDoc["_source"]["file_name"],
                                    "file_url" : oneDoc["_source"]["file_download_url"],
                                    "post_date": oneDoc["_source"]["post_date"],
                                    "post_writer": oneDoc["_source"]["post_writer"],
                                    "published_institution_url": oneDoc["_source"]["published_institution_url"],
                                    "top_category": oneDoc["_source"]["top_category"],
                                    "hlight_content": hlight_content
                                }
                             )
            except KeyError:    # 통일부 발간물 사이트의 경우 published_date가 존재하고 post_date가 없기에 생긴 코드
                corpus.append(
                    {
                        "_id": oneDoc["_id"],
                        "post_title": oneDoc["_source"]["post_title"],
                        "content": oneDoc["_source"]["file_extracted_content"],
                        "file_name": oneDoc["_source"]["file_name"],
                        "file_url": oneDoc["_source"]["file_download_url"],
                        "post_date": oneDoc["_source"]["published_date"],
                        "post_writer": oneDoc["_source"]["post_writer"],
                        "published_institution_url": oneDoc["_source"]["published_institution_url"],
                        "top_category": oneDoc["_source"]["top_category"],
                        "hlight_content": hlight_content
                    }
                )

        else:
            hlight_content = hlight.hlight_term(oneDoc['_source']['post_body'], temp_query)
            try:
                corpus.append(
                    {
                        "_id": oneDoc["_id"],
                        "post_title": oneDoc["_source"]["post_title"],
                        "content": oneDoc["_source"]["post_body"],
                        "post_date": oneDoc["_source"]["post_date"],
                        "post_writer": oneDoc["_source"]["post_writer"],
                        "published_institution_url": oneDoc["_source"]["published_institution_url"],
                        "top_category": oneDoc["_source"]["top_category"],
                        "hlight_content": hlight_content
                    }
                )
            except KeyError:    # 통일부 발간물 사이트의 경우 published_date가 존재하고 post_date가 없기에 생긴 코드
                corpus.append(
                    {
                        "_id": oneDoc["_id"],
                        "post_title": oneDoc["_source"]["post_title"],
                        "content": oneDoc["_source"]["file_extracted_content"],
                        "post_date": oneDoc["_source"]["published_date"],
                        "post_writer": oneDoc["_source"]["post_writer"],
                        "published_institution_url": oneDoc["_source"]["published_institution_url"],
                        "top_category": oneDoc["_source"]["top_category"],
                        "hlight_content": hlight_content
                    }
                )
    #print(corpus)
    return corpus


def elasticsearchGetDocs(total, temp_query):
    data = nkdbContent(total, temp_query)

    return data
