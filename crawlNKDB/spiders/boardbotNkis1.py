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
import time
time.sleep(0.5)
class BoardbotNkis1Spider(scrapy.Spider):
    name = 'boardbotNkis1'

    def __init__(self):
        scrapy.Spider.__init__(self)
        self.client = pymongo.MongoClient(config['DB']['MONGO_URI'])
        self.db = self.client['attchment']
        self.fs = gridfs.GridFS(self.db)
        jarpath = os.path.join(os.path.abspath('.'), './../lib/hwp-crawl.jar')
        jpype.startJVM(jpype.getDefaultJVMPath(), "-Djava.class.path=%s" % jarpath)

    # function1: start_requests(self)
    # 크롤링 시작할 url 설정, start_requests 함수에서 별도의 콜백함수를 구현해서 크롤링

    def start_requests(self):
        start_url = "http://www.nkis.kr/board.php?board=nkisb501"
        yield scrapy.Request(url = start_url, callback = self.parse, meta={'start_url':start_url})


    ### 수정이 필요하다 ###
    # function2: parse(self, response)
    # board의 각 page 접근요청하는 함수
    def parse(self, response):
        start_url = response.meta['start_url']
        response = requests.get(start_url)
        source = response.text
        soup = BeautifulSoup(source, 'html.parser')

        maximum = 0
        page = 2
        while True:
            page_list = soup.findAll("a", {"class": "page_number", "href": 'board.php?board=nkisb501&no=&command=list&page=' + str(page)})
            if not page_list:
                maximum = page - 1
                break
            page = page + 1

        page_no = 1
        last_page_no = maximum
        # print("last_page_no >>> ", last_page_no)
        while True:
            if page_no > last_page_no:
                break
            link = "http://www.nkis.kr/board.php?board=nkisb501&page=" + str(page_no)
            # print(link)
            yield scrapy.Request(link, callback = self.parse_each_pages, meta={'page_no': page_no, 'last_page_no': last_page_no})
            page_no += 1

    # function3: def parse_each_pages(self, response)
    # 페이지의 각 category 접근요청하는 함수
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
            category_link = response.xpath('//*[@id="mainIndexTable"]/tbody/tr[' + str(2*category_no) + ']/td[4]/a/@href').get()
            # print(category_link)
            url = 'http://www.nkis.kr/' + category_link
            yield scrapy.Request(url, callback=self.parse_category)
            category_no += 1

    # function4: def parse_category(self, response)
    # 각 category에 접근해 필요한 data를 크롤링하는 함수
    # parse_category 수정 + 4유형 + 1유형 넣기
    def parse_category(self, response):
        item = NkisboardItem()
        post_titles = response.xpath('//*[@id="mainIndexTable"]/tbody/tr[' + str(2*category_no) + ']/td[4]/a/span/text()').get()
        post_writers = response.xpath('//*[@id="mainIndexTable"]/tbody/tr[' + str(2*category_no) + ']/td[6]/span/text()').get()
        post_dates = response.xpath('//*[@id="mainIndexTable"]/tbody/tr[' + str(2*category_no) + ']/td[7]/nobr/text()').get()
        top_categorys = response.xpath('//*[@id="subLayer5"]/div/table/tr/td[3]/a/text()').get()
        body = response.css('#mainTextBodyDiv table:nth-child(3)')\
            .xpath('string()')\
            .extract()
        item['published_institution'] = 'North Korea Intellectuals Solidarity'
        item['published_institution_url'] = 'http://www.nkis.kr/'
        body_text = ''.join(body).replace("\r", "").replace("\n", """
        """).replace("\t", "").replace('\"', '"')
        item['post_body'] = body_text

        item[config['VARS']['VAR1']] = post_titles
        item[config['VARS']['VAR3']] = post_writers
        item[config['VARS']['VAR4']] = post_dates
        item[config['VARS']['VAR7']] = top_categorys

        yield item
