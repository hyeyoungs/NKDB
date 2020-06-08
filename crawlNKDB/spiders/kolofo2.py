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

print("Start crawling~ SDG!!!")
### modify
class Kolofo2Spider(scrapy.Spider):
    ### modify
    name = 'kolofo2'
    ### modify
    start_urls = ['http://www.kolofo.org/?c=user&mcd=sub03_01']
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
    headers = {'User-Agent': user_agent}

    def __init__(self):
        scrapy.Spider.__init__(self)
        ### modify
        self.start_urls = 'http://www.kolofo.org/?c=user&mcd=sub03_01'
        self.client = pymongo.MongoClient(config['DB']['MONGO_URI'])
        self.db = self.client['attchment']
        self.fs = gridfs.GridFS(self.db)
        jarpath = os.path.join(os.path.abspath('../../..'), './../lib/hwp-crawl.jar')
        jpype.startJVM(jpype.getDefaultJVMPath(), "-Djava.class.path=%s" % jarpath)

    def start_requests(self):
        yield scrapy.Request(self.start_urls, headers=self.headers, callback = self.parse)

    def parse(self, response):
        response = requests.get(self.start_urls, headers=self.headers)
        response.encoding = 'utf-8'
        source = response.text
        soup = BeautifulSoup(source, 'html.parser')

        last_page_list = soup.findAll("a", {"title": '다음'})
        if not last_page_list:
            maximum = 0
            page = 2
            while True:
                ###modify
                page_list = soup.findAll("a", {"href": '/?c=user&mcd=sub03_01&cur_page=' + str(page)})
                if not page_list:
                    maximum = page - 1
                    break
                page = page + 1
            last_page_no = maximum
        # >> 있는 경우, 마지막 페이지까지 찾기
        else:
            # print(last_page_list)
            last_page_no = re.findall("\d+", str(last_page_list[0]))
            last_page_no = int(last_page_no[-2])

        page_no = 1
        # print("last_page_no >>> ", last_page_no)
        while True:
            if page_no > last_page_no:
                break
            ###modify
            link = "http://www.kolofo.org/?c=user&mcd=sub03_01&cur_page=" + str(page_no)
            print(link)
            yield scrapy.Request(link, headers=self.headers, callback=self.parse_each_pages,
                                 meta={'page_no': page_no, 'last_page_no': last_page_no})
            page_no += 1

    def parse_each_pages(self, response):
        page_no = response.meta['page_no']
        last_page_no = response.meta['last_page_no']

        last = response.xpath('//*[@id="frm"]/div/table/tbody/tr[1]/td[1]/text()').get()
        if page_no == last_page_no:
            first = 1
        else:
            first = response.xpath('//*[@id="frm"]/div/table/tbody/tr[10]/td[1]/text()').get()

        category_last_no = int(last) - int(first) + 1
        category_no = 1

        while 1:
            # 해당 url을  item에 넣어준다.
            if (category_no > category_last_no):
                break

            category_link = response.xpath(
                '//*[@id="frm"]/div/table/tbody/tr[' + str(category_no) + ']/td[2]/a/@href').get()
            url = "http://www.kolofo.org" + category_link
            # item 객체생성
            item = CrawlnkdbItem()
            # item url에 할당
            yield scrapy.Request(url, headers=self.headers, callback=self.parse_category, meta={'item': item})
            category_no += 1

    def parse_category(self, response):
        # 각 항목마다 bodys, titles, writers, dates를 가져온다.
        title = response.xpath('//*[@id="contents"]/div/div[2]/div[1]/table[1]/thead/tr/td').xpath('string()').get()
        date = response.xpath('//*[@id="contents"]/div/div[2]/div[1]/table[1]/tbody/tr[1]/td[2]').xpath('string()').get()
        writer = response.xpath('//*[@id="contents"]/div/div[2]/div[1]/table[1]/tbody/tr[1]/td[1]').xpath('string()').get()
        body = response.css('.cont') \
            .xpath('string()') \
            .get()
        ### modify
        top_category = "칼럼"
        published_institution = "남북물류포럼"
        item = response.meta['item']
        item["post_title"] = title
        item["post_date"] = date
        item["post_body"] = body
        item["post_writer"] = writer
        item["published_institution"] = published_institution
        item["published_institution_url"] = "http://www.kolofo.org/"
        item["top_category"] = top_category

        yield item

    def __del__(self):
        jpype.shutdownJVM()
