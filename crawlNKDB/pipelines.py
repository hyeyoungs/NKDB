# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import pymongo
#from scrapy.utils.project import get_project_settings
#from scrapy.exceptions import DropItem
#from scrapy import log
import logging
import sys

import configparser
config = configparser.ConfigParser()
config.read('./../lib/config.cnf')

sys.path.append(config['SERVER']['PATH_SPIDER'])
from crawl_script import mongo_collection, mongo_database

class CrawlnkdbPipeline(object):
    #collection_name = 'nuacboard' #
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=mongo_database
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        #self.db = self.client[crawl.mongo_database]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        #logger = logging.getLogger()
        valid = True
        for data in item:
            if not data:
                valid = False
                print("Add to MongoDB Fail!!!!")
                #raise DropItem("Missing {0}!".format(data))
        if valid:
            self.db[mongo_collection].insert(dict(item))
            #self.client.insert(dict(item))
            #logger.msg("Crawled data added to MongoDB dataset!", level=log.DEBUG, spider=spider)
        return item
