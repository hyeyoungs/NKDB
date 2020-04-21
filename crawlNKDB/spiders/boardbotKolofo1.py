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


class Boardbotkolofo1Spider(scrapy.Spider):
    name = 'boardbotKolofo1'
    # function1: start_requests(self)
    # 크롤링 시작할 url 설정, start_requests 함수에서 별도의 콜백함수를 구현해서 크롤링
    def __init__(self):
        scrapy.Spider.__init__(self)
        self.client = pymongo.MongoClient(config['DB']['MONGO_URI'])
        self.db = self.client['attchment']
        self.fs = gridfs.GridFS(self.db)
        jarpath = os.path.join(os.path.abspath('.'), './../lib/hwp-crawl.jar')
        jpype.startJVM(jpype.getDefaultJVMPath(), "-Djava.class.path=%s" % jarpath)

    def start_requests(self):
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        headers = {'User-Agent': user_agent}
        start_url = "http://www.kolofo.org/?c=user&mcd=sub03_02"
        yield scrapy.Request(url = start_url, headers=headers, callback = self.parse, meta={'start_url':start_url})

    # function2: parse(self, response)
    # board의 각 page 접근요청하는 함수
    def parse(self, response):
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        headers = {'User-Agent': user_agent}
        start_url = response.meta['start_url']
        response = requests.get(start_url, headers=headers)
        response.encoding = 'utf-8'
        source = response.text
        soup = BeautifulSoup(source, 'html.parser')

        last_page_list = soup.findAll("a", {"title": '다음'})
        if not last_page_list:
            maximum = 0
            page = 2
            while True:
                page_list = soup.findAll("a", {"href": '/?c=user&mcd=sub03_02&cur_page=' + str(page)})
                if not page_list:
                    maximum = page - 1
                    break
                page = page + 1
            last_page_no = maximum
        # >> 있는 경우, 마지막 페이지까지 찾기
        else:
            # print(last_page_list)
            last_page_no = re.findall("\d+", str(last_page_list[0]))
            last_page_no = int(last_page_no[-2])

        page_no = 1
        # print("last_page_no >>> ", last_page_no)
        while True:
            if page_no > last_page_no:
                break
            link = "http://www.kolofo.org/?c=user&mcd=sub03_02&cur_page=" + str(page_no)
            # print(link)
            yield scrapy.Request(link, headers = headers, callback = self.parse_each_pages, meta={'page_no': page_no, 'last_page_no': last_page_no})
            page_no += 1

    # function3: def parse_each_pages(self, response)
    # 페이지의 각 category 접근요청하는 함수
    def parse_each_pages(self, response):
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        headers = {'User-Agent': user_agent}
        page_no = response.meta['page_no']
        last_page_no = response.meta['last_page_no']

        last = response.xpath('//*[@id="frm"]/div/table/tbody/tr[1]/td[1]/text()').get()
        if page_no == last_page_no:
            first = 1
        else:
            first = response.xpath('//*[@id="frm"]/div/table/tbody/tr[10]/td[1]/text()').get()

        category_last_no = int(last) - int(first)+1
        category_no = 1

        while 1:
        # 해당 url을  item에 넣어준다.
            if(category_no > category_last_no):
                break

            category_link = response.xpath('//*[@id="frm"]/div/table/tbody/tr[' + str(category_no) + ']/td[2]/a/@href').get()
            url =  "http://www.kolofo.org" + category_link
 			# item 객체생성
            item = CrawlnkdbItem()
 			# item url에 할당
            yield scrapy.Request(url, headers = headers, callback=self.parse_category, meta={'item':item})
            category_no += 1

    # * function4 각 항목마다 bodys, titles, writers, dates를 가져온다. def parse_category(self, response):
    def parse_category(self, response):
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        headers = {'User-Agent': user_agent}
	# 각 항목마다 bodys, titles, writers, dates를 가져온다.
        title = response.xpath('//*[@id="contents"]/div/div[2]/div[1]/table[1]/thead/tr/td/text()').get()
        date =response.xpath('//*[@id="contents"]/div/div[2]/div[1]/table[1]/tbody/tr[1]/td[2]/text()').get()
        writer =response.xpath('//*[@id="contents"]/div/div[2]/div[1]/table[1]/tbody/tr[1]/td[1]/text()').get()
        body =response.css('.cont').xpath('string()').get()
        top_category = response.xpath('//*[@id="contents"]/div/div[2]/h3/text()').get()
        published_institution = "남북물류포럼"
        item = response.meta['item']
        item[config['VARS']['VAR1']] = title
        item[config['VARS']['VAR4']] = date
        item[config['VARS']['VAR2']] = body
        item[config['VARS']['VAR3']] = writer
        item[config['VARS']['VAR5']] = published_institution
        item[config['VARS']['VAR6']]= "http://www.kolofo.org/"
        item[config['VARS']['VAR7']] = top_category

        ### 4유형 + 1유형 ###
        file_icon = response.xpath('//*[@id="contents"]/div/div[2]/div/table[1]/tbody/tr[2]/td/a/text()').get()
        if file_icon:
            file_download_url = response.xpath('//*[@id="contents"]/div/div[2]/div/table[1]/tbody/tr[2]/td/a/@href').extract()
            file_download_url = "http://www.kolofo.org/" + file_download_url[0]
            item[config['VARS']['VAR10']] = file_download_url
            file_name = response.xpath('//*[@id="contents"]/div/div[2]/div/table[1]/tbody/tr[2]/td/a/text()').get()
            item[config['VARS']['VAR9']] = file_name
            print("@@@@@@file name ", file_name)
            if file_icon.find("hwp") != -1 :
                print('find hwp')
                yield scrapy.Request(file_download_url, headers = headers, callback=self.save_file_hwp, meta={'item':item}) #
            else:
                yield scrapy.Request(file_download_url, headers = headers, callback=self.save_file, meta={'item':item})
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
