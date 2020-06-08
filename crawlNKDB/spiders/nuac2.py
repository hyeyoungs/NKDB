# -*- coding: utf-8 -*-
import scrapy
import os
import jpype
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
### modify
class Nuac2Spider(scrapy.Spider):
    ### modify
    name = 'nuac2'
    ### modify
    start_urls = ['http://www.nuac.go.kr/actions/BbsDataAction?cmd=list&_max=5&menuid=G060519&bbs_id=G060539&_template=ebook']

    def __init__(self):
        scrapy.Spider.__init__(self)
        ### modify
        self.start_urls = 'http://www.nuac.go.kr/actions/BbsDataAction?cmd=list&_max=5&menuid=G060519&bbs_id=G060539&_template=ebook'
        self.client = pymongo.MongoClient(config['DB']['MONGO_URI'])
        self.db = self.client['attchment']
        self.fs = gridfs.GridFS(self.db)
        jarpath = os.path.join(os.path.abspath('.'), './../lib/hwp-crawl.jar')
        jpype.startJVM(jpype.getDefaultJVMPath(), "-Djava.class.path=%s" % jarpath)

    def start_requests(self):
        yield scrapy.Request(self.start_urls, self.parse)

    def parse(self, response):
        total_page_text = response.xpath('//*[@id="stxt"]/text()').get()
        # print(total_page_text)
        last_page_no = re.findall("\d+", str(total_page_text))
        page_no = 1
        # last_page_no[-1]
        last_page_no = int(last_page_no[-1])
        while True:
            if page_no > last_page_no:
                break
            ### modify
            link = "http://www.nuac.go.kr/actions/BbsDataAction?cmd=list&menuid=G060519&bbs_num=&bbs_id=G060539&bbs_idx=&order=&ordertype=&oldmenu=&parent_idx=&_max=5&_page=" + str(page_no) + "&_template=ebook&searchtype=bbs_title&keyword=&name_confirm=&real_name="
            # print(link)
            yield scrapy.Request(link, callback = self.parse_each_pages, meta={'page_no': page_no, 'last_page_no': last_page_no})
            page_no += 1

    def parse_each_pages(self, response):
        page_no = response.meta['page_no']
        last_page_no = response.meta['last_page_no']
        ### modify
        last = response.xpath('//*[@id="main"]/div/div[2]/div/div[4]/table[2]/tbody/tr[1]/td[1]/div/font/text()').get()
        if page_no == last_page_no:
            category_last_no = int(last)
        else:
            ### modify
            first = response.xpath('//*[@id="main"]/div/div[2]/div/div[4]/table[2]/tbody/tr[5]/td[1]/div/font/text()').get()
            category_last_no = int(last) - int(first) + 1
        category_no = 1
        while True:
            if(category_no > category_last_no):
                break
            item = CrawlnkdbItem()
            ### modify
            title = response.xpath('//*[@id="main"]/div/div[2]/div/div[4]/table[2]/tbody/tr['+str(category_no)+']/td[3]/div').xpath('string()').get()
            body = " "
            writer = "관리자"
            date = response.xpath('//*[@id="main"]/div/div[2]/div/div[4]/table[2]/tbody/tr['+str(category_no)+']/td[6]/div/font').xpath('string()').get()
            top_category = response.xpath('//*[@id="main"]/div/div[1]/div[1]/a').xpath('string()').get()

            item[config['VARS']['VAR1']] = title
            item[config['VARS']['VAR2']] = body
            item[config['VARS']['VAR3']] = writer
            item[config['VARS']['VAR4']] = date
            item[config['VARS']['VAR5']] = "민주평화통일자문회의"
            item[config['VARS']['VAR6']] = "http://www.nuac.go.kr/actions/"
            item[config['VARS']['VAR7']] = top_category

            ### modify
            file_name = title
            file_download_url = response.xpath('//*[@id="main"]/div/div[2]/div/div[4]/table[2]/tbody/tr['+str(category_no)+']/td[5]/div/a/@href').get()
            category_no += 1
            if file_download_url is not None:
                item[config['VARS']['VAR10']] = file_download_url
                item[config['VARS']['VAR9']] = file_name
                #print("@@@@@@file name ", file_name)
                if file_download_url.find("hwp") != -1 :
                    #print('find hwp')
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
