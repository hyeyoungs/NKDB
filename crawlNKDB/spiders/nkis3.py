# -*- coding: utf-8 -*-
import jpype
import scrapy
import os
import sys
from crawlNKDB.items import CrawlnkdbItem
import re
import pymongo
from pymongo import MongoClient
import gridfs
from tika import parser
from tempfile import NamedTemporaryFile
from itertools import chain
control_chars = ''.join(map(chr, chain(range(0, 9), range(11, 32), range(127, 160))))
CONTROL_CHAR_RE = re.compile('[%s]' % re.escape(control_chars))

from bs4 import BeautifulSoup
import requests

import configparser
config = configparser.ConfigParser()
config.read('./../lib/config.cnf')

### modify
class Nkis3Spider(scrapy.Spider):
    name = 'nkis3'
    ### modify
    start_url = "http://www.nkis.kr/board.php?board=nkisb503"
    def __init__(self):
        scrapy.Spider.__init__(self)
        ### modify
        self.start_url = "http://www.nkis.kr/board.php?board=nkisb503"
        self.client = pymongo.MongoClient(config['DB']['MONGO_URI'])
        self.db = self.client['attchment']
        self.fs = gridfs.GridFS(self.db)
        jarpath = os.path.join(os.path.abspath('.'), './../lib/hwp-crawl.jar')
        jpype.startJVM(jpype.getDefaultJVMPath(), "-Djava.class.path=%s" % jarpath)

    def start_requests(self):
        yield scrapy.Request(self.start_url, self.parse)

    def parse(self, response):
        response = requests.get(self.start_url)
        source = response.text
        soup = BeautifulSoup(source, 'html.parser')

        maximum = 0
        page = 2
        while True:
            ### modify
            page_list = soup.findAll("a", {"class": "page_number", "href": 'board.php?board=nkisb503&no=&command=list&page=' + str(page)})
            if not page_list:
                maximum = page - 1
                break
            page = page + 1

        page_no = 1
        last_page_no = maximum
        print("last_page_no >>> ", last_page_no)

        while True:
            if page_no > last_page_no:
                break
            ### modify
            link = "http://www.nkis.kr/board.php?board=nkisb503&page=" + str(page_no)
            # print(link)
            yield scrapy.Request(link, callback = self.parse_each_pages, meta={'page_no': page_no, 'last_page_no': last_page_no})
            page_no += 1

    def parse_each_pages(self, response):
        page_no = response.meta['page_no']
        last_page_no = response.meta['last_page_no']
        last = response.xpath('//*[@id="mainIndexTable"]/tbody/tr[2]/td[2]/nobr/text()').get()

        if page_no == last_page_no:
            category_last_no = int(last)
        else:
            first = response.xpath('//*[@id="mainIndexTable"]/tbody/tr[32]/td[2]/nobr/text()').get()
            category_last_no = int(last) - int(first) + 1

        category_no = 1
        while True:
            if(category_no > category_last_no):
                break
            item = CrawlnkdbItem()
            post_title = response.xpath(
                '//*[@id="mainIndexTable"]/tbody/tr[' + str(2 * category_no) + ']/td[4]/a').xpath('string()').get()
            post_writer = response.xpath('//*[@id="mainIndexTable"]/tbody/tr[' + str(2*category_no) + ']/td[6]').xpath('string()').get()
            post_date = response.xpath('//*[@id="mainIndexTable"]/tbody/tr[' + str(2*category_no) + ']/td[7]').xpath('string()').get()
            item[config['VARS']['VAR1']] = post_title
            item[config['VARS']['VAR3']] = post_writer
            item[config['VARS']['VAR4']] = post_date

            print("###post_writer >>> ", post_writer)
            print("###post_date >>> ", post_date)

            category_link = response.xpath('//*[@id="mainIndexTable"]/tbody/tr[' + str(2*category_no) + ']/td[4]/a/@href').get()
            # print(category_link)
            url = 'http://www.nkis.kr/' + category_link
            print("###url >>> ", url)
            yield scrapy.Request(url, callback=self.parse_category, meta={'item':item})
            category_no += 1

    def parse_category(self, response):
        item = response.meta['item']
        top_category = "북한자료"
        body = response.css('#mainTextBodyDiv table:nth-child(3)') \
            .xpath('string()') \
            .extract()
        body = ''.join(body).replace("\r", "").replace("\n", """
                """).replace("\t", "").replace('\"', '"')

        print("###top_category >>> ", top_category)
        item[config['VARS']['VAR2']] = body
        item[config['VARS']['VAR5']] = 'NK지식인연대'
        item[config['VARS']['VAR6']] = 'http://www.nkis.kr/'
        item[config['VARS']['VAR7']] = top_category

        yield item

    def __del__(self):
        jpype.shutdownJVM()
