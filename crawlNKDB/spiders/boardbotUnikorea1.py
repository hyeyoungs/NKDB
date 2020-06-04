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
class Boardbotunikorea1Spider(scrapy.Spider):
    name = 'boardbotUnikorea1'
    #allowed_domains = ['unibook.unikorea.go.kr']
    start_urls = ['https://unibook.unikorea.go.kr/material/list?materialScope=ORIG&hasUrl=true']

    def __init__(self):
        scrapy.Spider.__init__(self)
        self.start_urls = 'https://unibook.unikorea.go.kr/material/list?materialScope=ORIG&hasUrl=true'
        self.client = pymongo.MongoClient(config['DB']['MONGO_URI'])
        self.db = self.client['attchment']
        self.fs = gridfs.GridFS(self.db)
        jarpath = os.path.join(os.path.abspath('../../..'), './../lib/hwp-crawl.jar')
        jpype.startJVM(jpype.getDefaultJVMPath(), "-Djava.class.path=%s" % jarpath)

    def start_requests(self):
        yield scrapy.Request(self.start_urls, self.parse)

    def parse(self, response):
        page_no = 1
        last_page_text = response.xpath('//*[@id="container"]/div/section/div[1]/div[2]/a[3]/@href').get()
        last_page_no = re.findall("\d+", str(last_page_text))
        last_page_no = int(last_page_no[-1])
        #print(last_page_no)
        while True:
            if page_no > last_page_no:
                break
            link = "https://unibook.unikorea.go.kr/material/list?materialScope=ORIG&hasUrl=true&page=" + str(page_no)
            #print(link)
            last = response.xpath('//*[@id="sublist"]/ul[1]/li[1]/div/label').xpath('string()').get()
            first = response.xpath('//*[@id="sublist"]/ul[10]/li[1]/div/label').xpath('string()').get()
            category_num = int(first) - int(last) + 1
            print(category_num)
            yield scrapy.Request(link, callback = self.parse_each_pages, meta={'page_no': page_no, 'last_page_no': last_page_no, 'category_num': category_num, 'link': link}, dont_filter = True)
            page_no += 1

    def parse_each_pages(self, response):
        link = response.meta['link']
        print("###link:  ", link)
        page_no = response.meta['page_no']
        last_page_no = response.meta['last_page_no']
        category_num = response.meta['category_num']
        print("###pageno:  ", page_no)

        if page_no == last_page_no:
            page_total_num = response.xpath('//*[@id="container"]/div/section/div[1]/div[1]/header/h5').xpath(
                'string()').get()
            page_total_num = re.findall("\d,\d+", str(page_total_num))
            page_total_num = str(page_total_num[0])
            page_total_num = page_total_num.replace(",", "")
            page_total_num = int(page_total_num)
            category_last_no = (last_page_no * category_num) - int(page_total_num)
            print(category_last_no)
        else:
            category_last_no = category_num

        category_no = 1
        while True:
            if(category_no > category_last_no):
                break
            title = response.xpath('//*[@id="sublist"]/ul[' + str(category_no) + ']/li[2]/h6/a').xpath('string()').get()
            print(title)
            body = " "
            writer = response.xpath('//*[@id="sublist"]/ul['+ str(category_no) + ']/li[2]/div/dl[1]/dd').xpath('string()').get()
            date = response.xpath('//*[@id="sublist"]/ul['+ str(category_no) +']/li[2]/div/dl[3]/dd').xpath('string()').get()

            item = CrawlnkdbItem()
            item[config['VARS']['VAR1']] = title
            item[config['VARS']['VAR2']] = body
            item[config['VARS']['VAR3']] = writer
            item[config['VARS']['VAR8']] = date
            item[config['VARS']['VAR7']] = "통일부 발간물"
            item[config['VARS']['VAR5']] = "통일부"
            item[config['VARS']['VAR6']] = "https://unibook.unikorea.go.kr/"
            item[config['VARS']['VAR9']] = title
            crawl_url = response.xpath('//*[@id="sublist"]/ul['+ str(category_no) + ']/li[2]/h6/a/@href').get()
            url = "https://unibook.unikorea.go.kr/material/" + crawl_url
            category_no += 1
            print("#############category_url", url)
            yield scrapy.Request(url, callback=self.parse_post, meta={'item':item})

    def parse_post(self, response):
        file_download_url = response.xpath('//*[@class="url_856_u btn-item-size btn-gray mr6 mb6"]/@href').get()
        print("###########file_download_url", file_download_url)
        item = response.meta['item']
        item[config['VARS']['VAR10']] = file_download_url
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
