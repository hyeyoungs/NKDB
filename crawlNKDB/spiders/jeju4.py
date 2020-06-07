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
class Jeju4Spider(scrapy.Spider):
    ### modify
    name = 'jeju4'
    allowed_domains = ['www.jpi.or.kr']
    ### modify
    start_urls = ['http://www.jpi.or.kr/kor/issue/reports.sky?code=working']

    def __init__(self):
        scrapy.Spider.__init__(self)
        ### modify
        self.start_urls = 'http://www.jpi.or.kr/kor/issue/reports.sky?code=working'
        self.client = pymongo.MongoClient(config['DB']['MONGO_URI'])
        self.db = self.client['attchment']
        self.fs = gridfs.GridFS(self.db)
        jarpath = os.path.join(os.path.abspath('../../..'), './../lib/hwp-crawl.jar')
        jpype.startJVM(jpype.getDefaultJVMPath(), "-Djava.class.path=%s" % jarpath)

    def start_requests(self):
        yield scrapy.Request(self.start_urls, self.parse)

    def last_page_category(self, link):
        response = requests.get(link)
        response.encoding = 'utf-8'
        source = response.text
        soup = BeautifulSoup(source, 'html.parser')
        li_list = soup.findAll("li", {"class": "title_01"})
        print(li_list)
        category_num = len(li_list)
        print("### num of last page category", category_num)
        return category_num

    def parse(self, response):
        page_no = 1
        last_page_text = response.xpath('//*[@id="pagenum"]/a[2]/@href').get()
        last_page_no = re.findall("\d+", str(last_page_text))
        last_page_no = int(last_page_no[-1])
        print(last_page_no)
        ### modify
        last_page_link = "http://www.jpi.or.kr/kor/issue/reports.sky?code=working&page=" + str(last_page_no) + "&"
        last_page_category_num = self.last_page_category(last_page_link)

        while True:
            if page_no > last_page_no:
                break
            ### modify
            link = "http://www.jpi.or.kr/kor/issue/reports.sky?code=working&page=" + str(page_no) + "&"
            #print(link)

            yield scrapy.Request(link, callback = self.parse_each_pages, meta={'page_no': page_no, 'last_page_no': last_page_no, 'link': link, 'last_page_category_num':last_page_category_num}, dont_filter = True)
            page_no += 1

    def parse_each_pages(self, response):
        link = response.meta['link']
        print("###link:  ", link)

        page_no = response.meta['page_no']
        print("###pageno:  ", page_no)
        last_page_no = response.meta['last_page_no']
        last_page_category_num = response.meta['last_page_category_num']

        if page_no == last_page_no:
            category_num = last_page_category_num
        else:
            category_num = 10
        category_no = 1
        while True:
            if(category_no > category_num):
                break
            title = response.xpath('//*[@id="sub_reports"]/ul[' + str(category_no) + ']/a/li').xpath('string()').get()
            print(title)
            writer = response.xpath('//*[@id="sub_reports"]/ul['+ str(category_no) +']/li[3]').xpath('string()').get()
            writer = writer.replace("By : ", "")
            writer = writer.strip()
            date = response.xpath('//*[@id="sub_reports"]/ul['+ str(category_no) +']/li[1]/span[1]').xpath('string()').get()
            date = date.replace("DATE : ", "")
            date = date.strip()

            item = CrawlnkdbItem()
            item[config['VARS']['VAR1']] = title
            item[config['VARS']['VAR3']] = writer
            item[config['VARS']['VAR4']] = date
            ### modify
            item[config['VARS']['VAR7']] = response.xpath('//*[@id="left_menu"]/li[4]/a').xpath('string()').get()
            item[config['VARS']['VAR5']] = "제주평화연구원"
            item[config['VARS']['VAR6']] = "http://www.jpi.or.kr/kor/issue/reports.sky"
            item[config['VARS']['VAR9']] = title
            crawl_url = response.xpath('//*[@id="sub_reports"]/ul['+ str(category_no) +']/a/@href').get()

            url = "http://www.jpi.or.kr" + crawl_url
            category_no += 1
            print("#############category_url", url)
            yield scrapy.Request(url, callback=self.parse_post, meta={'item':item})

    def parse_post(self, response):
        item = response.meta['item']

        body = response.xpath('//*[@class="cont"]').xpath('string()').get()
        print(body)
        item[config['VARS']['VAR2']] = body

        file_download_url = response.xpath('//*[@class="file"]/a/@href').get()
        file_download_url = "http://www.jpi.or.kr" + file_download_url
        print("###########file_download_url", file_download_url)
        item = response.meta['item']
        item[config['VARS']['VAR10']] = file_download_url
        file_icon = response.xpath('//*[@class="file"]/a/img/@src').get()
        if file_icon:
            if file_icon.find("hwp") != -1 :
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
