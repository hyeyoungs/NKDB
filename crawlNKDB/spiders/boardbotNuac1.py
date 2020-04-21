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
import time
time.sleep(0.5)
print("Start crawling~ SDG!!!")

class Boardbotnuac1Spider(scrapy.Spider):
    name = 'boardbotNuac1'
    allowed_domains = ['www.nuac.go.kr']
    start_urls = ['http://www.nuac.go.kr/actions/BbsDataAction?cmd=list&menuid=G020501&bbs_id=G020501&_template=01#']

    def __init__(self):
        scrapy.Spider.__init__(self)
        self.start_urls = 'http://www.nuac.go.kr/actions/BbsDataAction?cmd=list&menuid=G020501&bbs_id=G020501&_template=01#'
        self.client = pymongo.MongoClient(config['DB']['MONGO_URI'])
        self.db = self.client['attchment']
        self.fs = gridfs.GridFS(self.db)
        jarpath = os.path.join(os.path.abspath('.'), './../lib/hwp-crawl.jar')
        jpype.startJVM(jpype.getDefaultJVMPath(), "-Djava.class.path=%s" % jarpath)

    def start_requests(self):
        yield scrapy.Request(self.start_urls, self.parse)

    def parse(self, response):
        total_page_text = response.xpath('//*[@id="stxt"]/text()').extract()
        # print(total_page_text)
        last_page_no = re.findall("\d+", str(total_page_text))
        page_no = 1
        # last_page_no[-1]
        last_page_no = int(last_page_no[-1])
        while True:
            if page_no > last_page_no:
                break
            link = "http://www.nuac.go.kr/actions/BbsDataAction?cmd=list&menuid=G020501&bbs_num=&bbs_id=G020501&bbs_idx=&order=&ordertype=&nbss_id=&oldmenu=&virtualNo=&name=&writer_email=&ssn_md5=&confirm_key=&parent_idx=&head=&_max=&_page=" + str(page_no) + "&_template=01&searchtype=bbs_title&keyword=&name_confirm=&real_name="
            # print(link)
            yield scrapy.Request(link, callback = self.parse_each_pages, meta={'page_no': page_no, 'last_page_no': last_page_no})
            page_no += 1

    def parse_each_pages(self, response):
        page_no = response.meta['page_no']
        last_page_no = response.meta['last_page_no']
        last = response.xpath('//*[@id="main"]/table/tbody/tr[1]/td[1]/text()').get()
        if page_no == last_page_no:
            category_last_no = int(last)
        else:
            first = response.xpath('//*[@id="main"]/table/tbody/tr[10]/td[1]/text()').get()
            category_last_no = int(last) - int(first) + 1
        category_no = 1
        while True:
            if(category_no > category_last_no):
                break
            category_link = '//*[@id="main"]/table/tbody/tr['+ str(category_no) +']/td[2]/a'
            onclick_text = response.xpath(category_link).get()
            # print(onclick_text)
            number = response.xpath('//*[@id="main"]/table/tbody/tr['+ str(category_no) +']/td[1]/text()').get()
            url = re.findall("\d+" ,str(onclick_text))
            url = 'http://www.nuac.go.kr/actions/BbsDataAction?cmd=view&menuid=G' + url[1] + '&bbs_id=G' + url[1] + '&bbs_idx=' + url[0] + '&parent_idx=&_template=01&_max=&_page=' + str(page_no) + '&head='
            item = CrawlnkdbItem()
            yield scrapy.Request(url, callback=self.parse_post, meta={'item':item})
            category_no += 1

    def parse_post(self, response):
        title = response.css('#main > table > thead > tr > th font::text').get()
        body = response.css('.descArea').xpath('string()').get()
        top_categorys = response.xpath('//*[@id="left"]/ul/li[2]/ul/li[2]/a/text()').get()
        date = response.xpath('//*[@id="main"]/table/tbody/tr[3]/td[3]/text()').get()
        # 파일유무 차이가 난다.
        writer = response.xpath('//*[@id="main"]/table/tbody/tr[3]/td[5]/text()').get()
        item = response.meta['item']
        item[config['VARS']['VAR1']] = title
        item[config['VARS']['VAR4']] = date
        item[config['VARS']['VAR3']] = writer
        item[config['VARS']['VAR2']] = body
        item[config['VARS']['VAR5']] = "민주평화통일자문회의"
        item[config['VARS']['VAR6']] = "http://www.nuac.go.kr/actions/"
        item[config['VARS']['VAR7']] = top_categorys
        file_name = response.xpath('//*[@id="main"]/table/tbody/tr[1]/td[2]/a/text()').get()
        if file_name:
            #print("@@@@ file name contains hwp : ", file_name)
            file_download_url = response.xpath('//*[@id="main"]/table/tbody/tr[1]/td[2]/a/@href').extract() #
            file_download_url = "http://www.nuac.go.kr" + file_download_url[0]
            item[config['VARS']['VAR10']] = file_download_url
            item[config['VARS']['VAR9']] = file_name
            #print("@@@@@@file name ", file_name)
            if file_name.find("hwp") != -1 :
                #print('find hwp')
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
        # check saved status
        #temp_saving_file = "test_saving_fs.pdf"
        #with open(temp_saving_file, 'wb') as f:
        #    f.write(self.fs.get(file_id).read())
        #print("#################3", self.fs.get(file_id).read())
        tempfile = NamedTemporaryFile()
        tempfile.write(response.body)
        tempfile.flush()
        #print("tempfile.name is : ", tempfile.name)
        extracted_data = parser.from_file(tempfile.name)
        #print("@@@@@@@@@@@@@@@extracted_data is : ", extracted_data)
        extracted_data = extracted_data["content"]
        #print(type(extracted_data))
        if str(type(extracted_data)) == "<class 'str'>":
            extracted_data = CONTROL_CHAR_RE.sub('', extracted_data)
            extracted_data = extracted_data.replace('\n\n', '')
        #print("extracted_data is : ", extracted_data)
        #print("end file")
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
        #print(extracted_data)
        #print("###############get the hwp content###############")
        tempfile.close()
        item[config['VARS']['VAR12']] = extracted_data
        yield item

    def __del__(self):
        jpype.shutdownJVM()
