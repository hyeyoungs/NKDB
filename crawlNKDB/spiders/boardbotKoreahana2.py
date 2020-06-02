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

class Boardbotkoreahana2Spider(scrapy.Spider):
    name = 'boardbotKoreahana2'
    allowed_domains = ['www.koreahana.or.kr']
    start_urls = ['https://www.koreahana.or.kr/data_room/pro_data.jsp?sc_board_seq=60&sc_category_text=%EB%B0%95%EC%82%AC%EB%85%BC%EB%AC%B8&sc_searchCnd=title&page=1']

    def __init__(self):
        scrapy.Spider.__init__(self)
        self.start_urls = 'https://www.koreahana.or.kr/data_room/pro_data.jsp?sc_board_seq=60&sc_category_text=%EB%B0%95%EC%82%AC%EB%85%BC%EB%AC%B8&sc_searchCnd=title&page=1'
        self.client = pymongo.MongoClient(config['DB']['MONGO_URI'])
        self.db = self.client['attchment']
        self.fs = gridfs.GridFS(self.db)
        jarpath = os.path.join(os.path.abspath('.'), './../lib/hwp-crawl.jar')
        jpype.startJVM(jpype.getDefaultJVMPath(), "-Djava.class.path=%s" % jarpath)

    def start_requests(self):
        yield scrapy.Request(self.start_urls, self.parse)

    def parse(self, response):
        page_no = 1
        last_page_text = response.xpath('//*[@id="container"]/div[1]/div[2]/div[2]/div/div[6]/a[9]/@href').extract()
        last_page_no = re.findall("\d+", str(last_page_text))
        last_page_no = int(last_page_no[0])
        #print(last_page_no)
        while True:
            if page_no > last_page_no:
                break
            link = "https://www.koreahana.or.kr/data_room/pro_data.jsp?sc_board_seq=60&sc_category_text=%EB%B0%95%EC%82%AC%EB%85%BC%EB%AC%B8&sc_searchCnd=title&page="+str(page_no)
            #print(link)
            last = response.xpath('//*[@id="container"]/div[1]/div[2]/div[2]/div/div[4]/table/tbody/tr[1]/th/text()').get()
            first = response.xpath('//*[@id="container"]/div[1]/div[2]/div[2]/div/div[4]/table/tbody/tr[5]/th/text()').get()
            yield scrapy.Request(link, callback = self.parse_each_pages, meta={'page_no': page_no, 'last_page_no': last_page_no, 'last': last, 'first': first}, dont_filter = True)
            page_no += 1

    def parse_each_pages(self, response):
        page_no = response.meta['page_no']
        last_page_no = response.meta['last_page_no']
        last = response.meta['last']
        first = response.meta['first']
        if page_no == last_page_no:
            last = response.xpath('//*[@id="container"]/div[1]/div[2]/div[2]/div/div[4]/table/tbody/tr[1]/th/text()').get()
            category_last_no = int(last)
        else:
            category_last_no = int(last) - int(first) + 1
        category_no = 1
        while True:
            if(category_no > category_last_no):
                break
            item = CrawlnkdbItem()
            number = response.xpath('//*[@id="container"]/div[1]/div[2]/div[2]/div/div[4]/table/tbody/tr['+str(category_no)+']/th').get()
            #print(number)
            title = response.xpath('//*[@id="container"]/div[1]/div[2]/div[2]/div/div[4]/table/tbody/tr['+str(category_no)+']/td[1]/p/text()').get()
            # title = title.split(")", maxsplit=1)
            # title = title[1]
            # title = title.strip()
            # print(title)
            writer = "관리자"
            body = ""
            date = response.xpath('//*[@id="container"]/div[1]/div[2]/div[2]/div/div[4]/table/tbody/tr['+str(category_no)+']/td[1]/span[1]').xpath('string()').get()
            top_category = response.xpath('//*[@id="container"]/div[1]/div[2]/div[2]/div/div[2]/ul/li[3]/a').xpath('string()').get()
            item[config['VARS']['VAR1']] = title
            item[config['VARS']['VAR3']] = writer
            item[config['VARS']['VAR2']] = body
            item[config['VARS']['VAR4']] = date
            item[config['VARS']['VAR5']] = "남북하나재단"
            item[config['VARS']['VAR6']] = "https://www.koreahana.or.kr/"
            item[config['VARS']['VAR7']] = top_category
            file_name = title
            download_url = response.xpath('//*[@id="container"]/div[1]/div[2]/div[2]/div/div[4]/table/tbody/tr['+str(category_no)+']/td[2]/button/@onclick').get()
            download_url = download_url.split("'")
            # print(download_url)
            file_download_url = 'https://www.koreahana.or.kr' + download_url[1]
            print(file_download_url)
            item[config['VARS']['VAR10']] = file_download_url
            item[config['VARS']['VAR9']] = file_name
            category_no += 1

            yield scrapy.Request(file_download_url, callback=self.save_file, meta={'item':item})

    def save_file(self, response):
        item = response.meta['item']
        file_id = self.fs.put(response.body)
        item[config['VARS']['VAR11']] = file_id

        tempfile = NamedTemporaryFile()
        tempfile.write(response.body)
        tempfile.flush()

        extracted_data = parser.from_file(tempfile.name)
        extracted_data = extracted_data["content"]
        if str(type(extracted_data)) == "<class 'str'>":
            extracted_data = CONTROL_CHAR_RE.sub('', extracted_data)
            extracted_data = extracted_data.replace('\n\n', '')
        tempfile.close()
        print(extracted_data)
        item[config['VARS']['VAR12']] = extracted_data
        yield item

    def __del__(self):
        jpype.shutdownJVM()
