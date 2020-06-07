# -*- coding: utf-8 -*-
import os
import sys
from datetime import datetime

if __name__ == "__main__":
    date = datetime.today().strftime("%y%m%d")
    name = "nkdb"+date
    # ES inedx analyzer and mapping setting for mongodb data transporting
    os.system("curl -XPUT http://localhost:9200/" + name + "?pretty -H 'Content-Type: application/json' -d @setting.json")
    os.system("curl -XPUT http://localhost:9200/" + name + "/nkdb/_mapping?include_type_name=true -H 'Content-Type: application/json' -d @mapping.json")
    # execute transporter
    # os.system("transporter init mongodb elasticsearch")
    os.environ["MONGODB_URI"] = "mongodb://localhost/NKDB"
    command  = "echo $MONGODB_URI"
    os.system(command)
    os.environ["ELASTICSEARCH_URI"] = "http://localhost:9200/" + name
    command = "echo $ELASTICSEARCH_URI"
    os.system(command)
    # os.system("export ELASTICSEARCH_URI='http://localhost:9200/" + name + "'")
    os.system("transporter run pipeline.js")
    print("Success transporting the data from MongoDB to Elasticsearch")



