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
class Boardbotunikorea7Spider(scrapy.Spider):
    name = 'boardbotUnikorea7'
    #allowed_domains = ['unibook.unikorea.go.kr']
    start_urls = ['https://unibook.unikorea.go.kr/board/list?boardId=15']

    def __init__(self):
        scrapy.Spider.__init__(self)
        self.start_urls = 'https://unibook.unikorea.go.kr/board/list?boardId=15'
        self.client = pymongo.MongoClient(config['DB']['MONGO_URI'])
        self.db = self.client['attchment']
        self.fs = gridfs.GridFS(self.db)
        jarpath = os.path.join(os.path.abspath('.'), './../lib/hwp-crawl.jar')
        jpype.startJVM(jpype.getDefaultJVMPath(), "-Djava.class.path=%s" % jarpath)

    def start_requests(self):
        yield scrapy.Request(self.start_urls, self.parse)

    def parse(self, response):
        page_no = 1
        last_page_text = response.xpath('//*[@id="container"]/div/section/div[1]/div[3]/button[3]/@onclick').get()
        last_page_no = re.findall("\d+", str(last_page_text))
        last_page_no = int(last_page_no[-1])
        #print(last_page_no)
        while True:
            if page_no > last_page_no:
                break
            link = "https://unibook.unikorea.go.kr/board/list?boardId=15&categoryId=&page="+str(page_no) + "&id=&field=searchAll&searchInput="
            #print(link)
            last = response.xpath('//*[@id="container"]/div/section/div[1]/table/tbody/tr[1]/td[1]/text()').get()
            first = response.xpath('//*[@id="container"]/div/section/div[1]/table/tbody/tr[10]/td[1]/text()').get()
            yield scrapy.Request(link, callback = self.parse_each_pages, meta={'page_no': page_no, 'last_page_no': last_page_no, 'last': last, 'first': first}, dont_filter = True)
            page_no += 1

    def parse_each_pages(self, response):
        page_no = response.meta['page_no']
        last_page_no = response.meta['last_page_no']
        last = response.meta['last']
        first = response.meta['first']
        print("###pageno:  ", page_no)
        print(last)
        print(first)
        if page_no == last_page_no:
            category_last_no = int(last)
        else:
            category_last_no = int(last) - int(first) + 1
        category_no = 1
        while True:
            if(category_no > category_last_no):
                break
            category_link = response.xpath('//*[@id="container"]/div/section/div[1]/table/tbody/tr[' + str(category_no) + ']/td[2]/a/@onclick').get()
            category_link_no = re.findall("\d+", str(category_link))
            category_link_no = int(category_link_no[-1])

            url = 'https://unibook.unikorea.go.kr/board/view?boardId=20&categoryId=&page=&id='+ str(category_link_no) +'&field=searchAll&searchInput='
            item = CrawlnkdbItem()
            yield scrapy.Request(url, callback=self.parse_post)
            category_no += 1

    def parse_post(self, response):
        title = response.xpath('//*[@id="container"]/div/section/div[1]/div/table/tbody/tr[1]/td').xpath('string()').get()
        body = response.xpath('//*[@id="container"]/div/section/div[1]/div/table/tbody/tr[7]/td').xpath('string()').get()
        writer = response.xpath('//*[@id="container"]/div/section/div[1]/div/table/tbody/tr[4]/td').xpath('string()').get()
        date = response.xpath('//*[@id="container"]/div/section/div[1]/div/table/tbody/tr[6]/td').xpath('string()').get()
        top_category = response.xpath('//*[@id="container"]/div/section/header/h1').xpath('string()').get()
        print(top_category)
<<<<<<< HEAD
        item = CrawlnkdbItem()
=======
        item = response.meta['item']
>>>>>>> 3b38435add9fc728d4cfafda4967904c348fa24a
        item[config['VARS']['VAR1']] = title
        item[config['VARS']['VAR2']] = body
        item[config['VARS']['VAR3']] = writer
        item[config['VARS']['VAR4']] = date
        item[config['VARS']['VAR7']] = top_category
        item[config['VARS']['VAR5']] = "통일부"
        item[config['VARS']['VAR6']] = "https://unibook.unikorea.go.kr/"
        file_name = response.xpath('//*[@id="container"]/div/section/div[1]/div/table/tbody/tr[3]/td/a').xpath('string()').get()
        file_download_url = response.xpath('//*[@id="container"]/div/section/div[1]/div/table/tbody/tr[3]/td/a/@href').get()
        file_download_url = "https://unibook.unikorea.go.kr" + file_download_url
        print(file_download_url)
        item[config['VARS']['VAR10']] = file_download_url
        item[config['VARS']['VAR9']] = file_name
        print("@@@@@@file name ", file_name)
        if file_download_url:
            if file_download_url.find("hwp") != -1 :
                print('find hwp')
                yield scrapy.Request(file_download_url, callback=self.save_file_hwp, meta={'item':item}) #
            else:
                yield scrapy.Request(file_download_url, callback=self.save_file, meta={'item':item})
        else:
            #print("###############file does not exist#################")
            yield item

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
        item[config['VARS']['VAR12']] = extracted_data
        yield item


    def save_file_hwp(self, response):
        item = response.meta['item']
        file_id = self.fs.put(response.body)
        item[config['VARS']['VAR11']] = file_id

        tempfile = NamedTemporaryFile()
        tempfile.write(response.body)
        tempfile.flush()

        testPkg = jpype.JPackage('com.argo.hwp') # get the package
        JavaCls = testPkg.Main # get the class
        hwp_crawl = JavaCls() # create an instance of the class
        extracted_data = hwp_crawl.getStringTextFromHWP(tempfile.name)
        if str(type(extracted_data)) == "<class 'str'>":
            extracted_data = CONTROL_CHAR_RE.sub('', extracted_data)
            extracted_data = extracted_data.replace('\n\n', '')
        print(extracted_data)
        print("###############get the hwp content###############")
        tempfile.close()
        item[config['VARS']['VAR12']] = extracted_data
        yield item

    def __del__(self):
        jpype.shutdownJVM()
