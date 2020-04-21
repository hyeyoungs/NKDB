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
import time
time.sleep(0.5)
print("Start crawling~ SDG!!!")
###### 수정사항
class Boardbotkinu6Spider(scrapy.Spider):
    ###### 수정사항
    name = 'boardbotKinu6'
    allowed_domains = ['www.kinu.or.kr']
    ####### 수정사항
    start_urls = ['http://www.kinu.or.kr/www/jsp/prg/api/dlL.jsp?menuIdx=261&category=10&thisPage=1&searchField=&searchText=']

    def __init__(self):
        scrapy.Spider.__init__(self)
        ####### 수정사항
        self.start_urls = 'http://www.kinu.or.kr/www/jsp/prg/api/dlL.jsp?menuIdx=261&category=10&thisPage=1&searchField=&searchText='
        self.client = pymongo.MongoClient(config['DB']['MONGO_URI'])
        self.db = self.client['attchment']
        self.fs = gridfs.GridFS(self.db)
        jarpath = os.path.join(os.path.abspath('.'), './../lib/hwp-crawl.jar')
        jpype.startJVM(jpype.getDefaultJVMPath(), "-Djava.class.path=%s" % jarpath)

    def start_requests(self):
        yield scrapy.Request(self.start_urls, self.parse)

    def parse(self, response):
        page_no = 1
        last_page_text = response.xpath('//*[@id="boardActionFrm"]/div[1]/div[1]/span').extract()
        print(last_page_text)
        last_page_no = re.findall("\d+", str(last_page_text))
        print(last_page_no)
        last_page_no = int(last_page_no[-1])
        print(last_page_no)
        while True:
            if page_no > last_page_no:
                break
            ####### 수정사항
            link = "http://www.kinu.or.kr/www/jsp/prg/api/dlL.jsp?menuIdx=261&category=10&thisPage=" + str(page_no) + "&searchField=title&searchText="
            print(link)
            yield scrapy.Request(link, callback = self.parse_each_pages, meta={'page_no': page_no, 'last_page_no': last_page_no})
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
            number = response.xpath('//*[@id="boardActionFrm"]/div[2]/table/tbody/tr['+str(category_no)+']/td[1]').get()
            #print(number)
            item = CrawlnkdbItem()
            date = response.xpath('//*[@id="boardActionFrm"]/div[2]/table/tbody/tr['+str(category_no)+']/td[3]').xpath('string()').get()
            item[config['VARS']['VAR4']] = date
            yield scrapy.Request(url, callback=self.parse_post, meta={'item':item})
            category_no += 1

    def parse_post(self, response):
        title = response.xpath('//*[@id="cmsContent"]/div[1]/p').xpath('string()').get()
        body = response.css('#tab_con > div').xpath('string()').get()

        writer = response.css('#cmsContent > div.board_wrap_bbs > table > thead > tr:nth-child(1) > td').xpath('string()').get()
        top_category = response.css('#container > div.content > div.conTop > div > h2').xpath('string()').get()
        item = response.meta['item']
        item[config['VARS']['VAR1']] = title
        item[config['VARS']['VAR3']] = writer
        item[config['VARS']['VAR2']] = body
        item[config['VARS']['VAR5']] = "통일연구원"
        item[config['VARS']['VAR6']] = "http://www.kinu.or.kr/www/jsp/prg/"
        item[config['VARS']['VAR7']] = top_category
        file_name = title
        file_icon = response.xpath('//*[@id="cmsContent"]/div[2]/table/thead/tr[5]/td/a/img').get()
        if file_icon:
            file_download_url = response.xpath('//*[@id="cmsContent"]/div[2]/table/thead/tr[5]/td/a/@href').extract()
            file_download_url = file_download_url[0]
            item[config['VARS']['VAR10']] = file_download_url
            item[config['VARS']['VAR9']] = file_name
            print("@@@@@@file name ", file_name)
            if file_icon.find("hwp") != -1 :
                print('find hwp')
                yield scrapy.Request(file_download_url, callback=self.save_file_hwp, meta={'item':item}) #
            else:
                yield scrapy.Request(file_download_url, callback=self.save_file, meta={'item':item})
        else:
            print("###############file does not exist#################")
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
