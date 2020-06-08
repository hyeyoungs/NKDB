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
#######modify
class Peace6Spider(scrapy.Spider):
    #######modify
    name = 'peace6'
    #allowed_domains = ['www.pf.or.kr']
    #######modify
    start_urls = ['http://www.pf.or.kr/wpages/01-3_research_1.php?bbs_code=10001&bbs_cate=7']

    def __init__(self):
        scrapy.Spider.__init__(self)
        #######modify
        self.start_urls = 'http://www.pf.or.kr/wpages/01-3_research_1.php?bbs_code=10001&bbs_cate=7'
        self.client = pymongo.MongoClient(config['DB']['MONGO_URI'])
        self.db = self.client['attchment']
        self.fs = gridfs.GridFS(self.db)
        jarpath = os.path.join(os.path.abspath('../../..'), './../lib/hwp-crawl.jar')
        jpype.startJVM(jpype.getDefaultJVMPath(), "-Djava.class.path=%s" % jarpath)

    def start_requests(self):
        yield scrapy.Request(self.start_urls, self.parse)

    def parse(self, response):
        page_no = 1
        maximum_num = response.xpath('//*[@id="mci_entrep"]/table/tbody/tr[2]/td[1]').xpath('string()').get()
        print("#######maximum_num: ", maximum_num)
        maximum_num = int(maximum_num)
        if maximum_num % 10 == 0:
            last_page_no = int(maximum_num / 10)
        else :
            last_page_no = int(maximum_num / 10) + 1
        print("#######last_page_no: ", last_page_no)
        while True:
            if page_no > last_page_no:
                break
            #######modify
            link = "http://www.pf.or.kr/wpages/01-3_research_1.php?bbs_code=10001&bbs_cate=7&sypage=&page="+ str(page_no) +"&keyword=&search="
            #print(link)

            yield scrapy.Request(link, callback = self.parse_each_pages, meta={'page_no': page_no, 'last_page_no': last_page_no}, dont_filter = True)
            page_no += 1

    def parse_each_pages(self, response):
        page_no = response.meta['page_no']
        last_page_no = response.meta['last_page_no']
        print("###pageno:  ", page_no)

        last = response.xpath('//*[@id="mci_entrep"]/table/tbody/tr[2]/td[1]').xpath('string()').get()

        if page_no == last_page_no:
            print("###last ", last)
            category_last_no = int(last)
        else:
            category_last_no = 10

        category_no = 1
        while True:
            if (category_no > category_last_no):
                break
            category_p1 = category_no + 1
            category_link = response.xpath(
                '//*[@id="mci_entrep"]/table/tbody/tr[' + str(category_p1) + ']/td[2]/a/@href').get()
            print("###category_link ", category_link, category_p1)
            ### modify
            url = 'http://www.pf.or.kr/wpages/01-3_research_1.php' + category_link

            category_no += 1
            yield scrapy.Request(url, callback=self.parse_post)

    def parse_post(self, response):
        item = CrawlnkdbItem()

        title = response.xpath('//*[@id="mci_entrep"]/table/tbody/tr[1]/td').xpath('string()').get()
        body = response.xpath('//*[@id="mci_entrep"]/table/tbody/tr[5]').xpath('string()').get()
        writer = response.xpath('//*[@id="mci_entrep"]/table/tbody/tr[2]/td[1]').xpath('string()').get()
        date = response.xpath('//*[@id="mci_entrep"]/table/tbody/tr[2]/td[2]').xpath('string()').get()
        #######modify
        top_category = response.xpath('//*[@id="rep_tab_btn07"]/a').xpath('string()').get()

        item[config['VARS']['VAR1']] = title
        item[config['VARS']['VAR3']] = writer
        item[config['VARS']['VAR2']] = body
        item[config['VARS']['VAR4']] = date
        item[config['VARS']['VAR5']] = "평화재단"
        item[config['VARS']['VAR6']] = "http://www.pf.or.kr/wpages/01-3_research_1.php"
        item[config['VARS']['VAR7']] = top_category
        file_name = response.xpath('//*[@id="mci_entrep"]/table/tbody/tr[4]/td/a').xpath('string()').get()
        print("###file_name:  ", file_name)
        if file_name is not None:
            file_download_pre = response.xpath('//*[@id="mci_entrep"]/table/tbody/tr[4]/td/a/@href').get()
            file_download_url = "http://www.pf.or.kr" + file_download_pre
            item[config['VARS']['VAR10']] = file_download_url
            item[config['VARS']['VAR9']] = file_name
            item[config['VARS']['VAR12']] = body
            #print("@@@@@@file name ", file_name)
            yield item

    def __del__(self):
        jpype.shutdownJVM()
