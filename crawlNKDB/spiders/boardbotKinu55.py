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

import configparser
config = configparser.ConfigParser()
config.read('./../lib/config.cnf')

print("Start crawling~ SDG!!!")
###### 수정사항
class Boardbotkinu55Spider(scrapy.Spider):
    ###### 수정사항
    name = 'boardbotKinu55'
    allowed_domains = ['www.kinu.or.kr']
    ####### 수정사항
    start_urls = ['http://www.kinu.or.kr/www/jsp/prg/api/dlL3.jsp?menuIdx=377&category=64&thisPage=1&searchField=&searchText=']

    def __init__(self):
        scrapy.Spider.__init__(self)
        ####### 수정사항
        self.start_urls = 'http://www.kinu.or.kr/www/jsp/prg/api/dlL3.jsp?menuIdx=377&category=64&thisPage=1&searchField=&searchText='
        self.client = pymongo.MongoClient(config['DB']['MONGO_URI'])
        self.db = self.client['attchment']
        self.fs = gridfs.GridFS(self.db)
        jarpath = os.path.join(os.path.abspath('.'), './../lib/hwp-crawl.jar')
        jpype.startJVM(jpype.getDefaultJVMPath(), "-Djava.class.path=%s" % jarpath)

    def start_requests(self):
        yield scrapy.Request(self.start_urls, self.parse, dont_filter=True)

    def parse(self, response):
        page_no = 1
        last_page_text = response.xpath('//*[@id="boardActionFrm"]/div[1]/div[2]/span').extract()
        print(last_page_text)
        last_page_no = re.findall("\d+", str(last_page_text))
        print(last_page_no)
        last_page_no = int(last_page_no[-1])
        print(last_page_no)
        while True:
            if page_no > last_page_no:
                break
            ####### 수정사항
            link = "http://www.kinu.or.kr/www/jsp/prg/api/dlL3.jsp?menuIdx=377&category=64&thisPage=" + str(page_no) + "&searchField=&searchText="
            print(link)
            yield scrapy.Request(link, callback = self.parse_each_pages, meta={'page_no': page_no, 'last_page_no': last_page_no}, dont_filter=True)
            page_no += 1

    def parse_each_pages(self, response):
        page_no = response.meta['page_no']
        last_page_no = response.meta['last_page_no']
        print("###pageno:  ", page_no)
        last = response.xpath('//*[@id="boardActionFrm"]/div[2]/table/tbody/tr[1]/td[1]/text()').get()
        if page_no == last_page_no:
            category_last_no = int(last)
        else:
            first = response.xpath('//*[@id="boardActionFrm"]/div[2]/table/tbody/tr[10]/td[1]/text()').get()
            category_last_no = int(last) - int(first) + 1
        category_no = 1
        while True:
            if(category_no > category_last_no):
                break
            category_link = response.xpath('//*[@id="boardActionFrm"]/div[2]/table/tbody/tr['+ str(category_no) +']/td[2]/a/@href').get()
            url = 'http://www.kinu.or.kr/www/jsp/prg/api/' + category_link
            # print(url)
            #number = response.xpath('//*[@id="boardActionFrm"]/div[2]/table/tbody/tr['+str(category_no)+']/td[1]').get()
            #print(number)
            item = CrawlnkdbItem()
            date = response.xpath('//*[@id="boardActionFrm"]/div[2]/table/tbody/tr['+str(category_no)+']/td[3]').xpath('string()').get()
            item[config['VARS']['VAR4']] = date
            yield scrapy.Request(url, callback=self.parse_post, meta={'item':item})
            category_no += 1

    def parse_post(self, response):
        title = response.xpath('//*[@id="cmsContent"]/div[2]/p').xpath('string()').get()
        body = response.xpath('//*[@id="cmsContent"]/div[1]/div/div[2]').xpath('string()').get()
        writer = response.css('#cmsContent > div.board_wrap_bbs > table > thead > tr:nth-child(1) > td').xpath('string()').get()
        top_category = response.css('#container > div.content > div.conTop > div > h2').xpath('string()').get()
        item = response.meta['item']
        item[config['VARS']['VAR1']] = title
        item[config['VARS']['VAR3']] = writer
        item[config['VARS']['VAR2']] = body
        item[config['VARS']['VAR5']] = "통일연구원"
        item[config['VARS']['VAR6']] = "http://www.kinu.or.kr/www/jsp/prg/"
        item[config['VARS']['VAR7']] = top_category
        yield item

    def __del__(self):
        jpype.shutdownJVM()
