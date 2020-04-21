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
# 수정
class Boardbotnuac2Spider(scrapy.Spider):
    # 수정
    name = 'boardbotNuac2'
    allowed_domains = ['www.nuac.go.kr']
    # 수정
    start_urls = ['http://www.nuac.go.kr/actions/BbsDataAction?cmd=list&_max=5&menuid=G060519&bbs_id=G060539&_template=ebook']

    def __init__(self):
        scrapy.Spider.__init__(self)
        self.start_urls = 'http://www.nuac.go.kr/actions/BbsDataAction?cmd=list&_max=5&menuid=G060519&bbs_id=G060539&_template=ebook'
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
            # 수정
            link = "http://www.nuac.go.kr/actions/BbsDataAction?cmd=list&menuid=G060519&bbs_num=&bbs_id=G060539&bbs_idx=&order=&ordertype=&oldmenu=&parent_idx=&_max=5&_page=" + str(page_no) + "&_template=ebook&searchtype=bbs_title&keyword=&name_confirm=&real_name="
            # print(link)
            yield scrapy.Request(link, callback = self.parse_each_pages, meta={'page_no': page_no, 'last_page_no': last_page_no})
            page_no += 1

    def parse_each_pages(self, response):
        page_no = response.meta['page_no']
        last_page_no = response.meta['last_page_no']
        # 수정
        last = response.xpath('//*[@id="main"]/div/div[2]/div/div[4]/table[2]/tbody/tr[1]/td[1]/div/font/text()').get()
        if page_no == last_page_no:
            category_last_no = int(last)
        else:
            # 수정
            first = response.xpath('//*[@id="main"]/div/div[2]/div/div[4]/table[2]/tbody/tr[5]/td[1]/div/font/text()').get()
            category_last_no = int(last) - int(first) + 1
        category_no = 1
        while True:
            if(category_no > category_last_no):
                break
            item = CrawlnkdbItem()
            ##### 수정이 필요 #####
            title = response.xpath('//*[@id="main"]/div/div[2]/div/div[4]/table[2]/tbody/tr[1]/td[3]/div').xpath('string()').get()
            body = ""
            top_category = response.xpath('//*[@id="left"]/ul/li[4]/ul/li[2]/a/text()').get()
            ebook = response.xpath('//*[@id="main"]/div/div[2]/div/div[4]/table[2]/tbody/tr[1]/td[4]/div/img/@src').get()
            if ebook:
                date = response.xpath('//*[@id="main"]/div/div[2]/div/div[4]/table[2]/tbody/tr[1]/td[6]/text()').get()
            else:
                date = response.xpath('//*[@id="main"]/div/div[2]/div/div[4]/table[2]/tbody/tr[1]/td[5]/text()').get()

            # 파일유무 차이가 난다.
            writer = "관리자"
            item[config['VARS']['VAR1']] = title
            item[config['VARS']['VAR4']] = date
            item[config['VARS']['VAR3']] = writer
            item[config['VARS']['VAR2']] = body
            item[config['VARS']['VAR5']] = "민주평화통일자문회의"
            item[config['VARS']['VAR6']] = "http://www.nuac.go.kr/actions/"
            item[config['VARS']['VAR7']] = top_category

            ##### 수정이 필요 #####
            file_name = response.xpath('//*[@id="main"]/div/div[2]/div/div[4]/table[2]/tbody/tr[1]/td[3]/div').xpath('string()').get()
            category_no += 1
            if file_name:
                if ebook:
                    file_download_url = response.xpath('//*[@id="main"]/div/div[2]/div/div[4]/table[2]/tbody/tr[2]/td[5]/div/a/@href').get()
                else:
                    file_download_url = response.xpath('//*[@id="main"]/div/div[2]/div/div[4]/table[2]/tbody/tr[1]/td[4]/div/a/@href').get()
                print(file_download_url)
                item[config['VARS']['VAR10']] = file_download_url
                item[config['VARS']['VAR9']] = file_name
                #print("@@@@@@file name ", file_name)
                if file_name.find("hwp") != -1 :
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
