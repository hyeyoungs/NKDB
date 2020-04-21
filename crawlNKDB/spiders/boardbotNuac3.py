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

print("Start crawling~ SDG!!!")

class Boardbotnuac2Spider(scrapy.Spider):
    name = 'boardbotNuac3'
    allowed_domains = ['www.nuac.go.kr']
    start_urls = ['http://www.nuac.go.kr/actions/BbsDataAction?cmd=list&menuid=G060519&bbs_id=G060549&_template=ebook&_max=5']

    def __init__(self):
        scrapy.Spider.__init__(self)
        self.start_urls = 'http://www.nuac.go.kr/actions/BbsDataAction?cmd=list&menuid=G060519&bbs_id=G060549&_template=ebook&_max=5'
        self.client = pymongo.MongoClient('mongodb://localhost:27017')
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
            link = "http://www.nuac.go.kr/actions/BbsDataAction?cmd=list&menuid=G060519&bbs_num=&bbs_id=G060549&bbs_idx=&order=&ordertype=&oldmenu=&parent_idx=&_max=5&_page=" + str(page_no) + "&_template=ebook&searchtype=bbs_title&keyword=&name_confirm=&real_name="
            # print(link)
            yield scrapy.Request(link, callback = self.parse_each_pages, meta={'page_no': page_no, 'last_page_no': last_page_no})
            page_no += 1

    def parse_each_pages(self, response):
        page_no = response.meta['page_no']
        last_page_no = response.meta['last_page_no']
        last = response.xpath('//*[@id="main"]/div/div[2]/div/div[4]/table[2]/tbody/tr[1]/td[1]/div/font/text()').get()
        if page_no == last_page_no:
            category_last_no = int(last)
        else:
            first = response.xpath('//*[@id="main"]/div/div[2]/div/div[4]/table[2]/tbody/tr[5]/td[1]/div/font/text()').get()
            category_last_no = int(last) - int(first) + 1
        category_no = 1
        while True:
            if(category_no > category_last_no):
                break
            url = response.xpath('//*[@id="main"]/div/div[2]/div/div[4]/table[2]/tbody/tr[' + str(category_no) + ']/td[3]/div/a/@href').get()
            item = CrawlnkdbItem() #
            yield scrapy.Request(url, callback=self.parse_post, meta={'item':item})
            category_no += 1

    def parse_post(self, response):
        title = response.css('#main > div > div.seaTabs01_content > div > div:nth-child(4) > table.boardtype1 > tbody > tr:nth-child(1) > td:nth-child(3) > div > a > font::text').get()
        # table_text = response.css('#main > table > tbody > tr.boardview2 td::text').extract()
        body = response.css('.descArea').xpath('string()').get()
        top_categorys = response.xpath('//*[@id="left"]/ul/li[4]/ul/li[2]/a/text()').get()
        date = response.xpath('//*[@id="main"]/div/div[2]/div/div[4]/table[2]/tbody/tr[' + str(category_no) + ']/td[5]/div/font/text()').get()
        # for text in table_text:
        #     if "등록일" in text:
        #         date = text
        item = response.meta['item']
        item['post_title'] = title.strip()
        item['post_date'] = date.strip()
        item['post_body'] = body.strip()
        item['published_institution'] = "민주평화통일자문회의"
        item['published_institution_url'] = "http://www.nuac.go.kr/actions/"
        item['top_category'] = top_categorys.strip()
        file_name = title
        if file_name:
            print("@@@@ file name contains hwp : ", file_name)
            file_download_url = '//*[@id="main"]/div/div[2]/div/div[4]/table[2]/tbody/tr[' + category_no + ']/td[4]/div/a/@href'
            file_download_url = response.xpath(file_download_url).extract()
            file_download_url = "http://www.nuac.go.kr" + file_download_url[0]
            item['file_download_url'] = file_download_url
            item['file_name'] = file_name.strip()
            print("@@@@@@file name ", file_name)
            if file_name.find("hwp") != -1 :
                self.hwp_count += 1
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
        item['file_id_in_fsfiles'] = file_id
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
        item['file_extracted_content'] = extracted_data
        yield item


    def save_file_hwp(self, response):
        item = response.meta['item']
        file_id = self.fs.put(response.body)
        item['file_id_in_fsfiles'] = file_id

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
        item['file_extracted_content'] = extracted_data
        yield item

    def __del__(self):
	    jpype.shutdownJVM()
