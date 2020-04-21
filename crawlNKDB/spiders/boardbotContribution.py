# -*- coding: utf-8 -*-
import scrapy
import re
from crawlNKDB.items import CrawlnkdbItem

from bs4 import BeautifulSoup
import requests

import configparser
config = configparser.ConfigParser()
config.read('./../lib/config.cnf')


class BoardbotcontributionSpider(scrapy.Spider):
    name = 'boardbotContribution'

    # function1: start_requests(self)
    # 크롤링 시작할 url 설정, start_requests 함수에서 별도의 콜백함수를 구현해서 크롤링
    def start_requests(self):
        start_url = "http://www.nkorea.or.kr/board/index.html?id=coulmn"
        yield scrapy.Request(url = start_url, callback = self.parse, meta={'start_url':start_url})

    # function2: parse(self, response)
    # board의 각 page 접근요청하는 함수
    def parse(self, response):
        start_url = response.meta['start_url']
        response = requests.get(start_url)
        # response.encoding = 'utf-8'
        source = response.text
        soup = BeautifulSoup(source, 'html.parser')
        page = 2
        while True:
            page_list = soup.findAll("a", {"href": '?id=coulmn&page=' + str(page)})
            if not page_list:
                maximum = page - 1
                break
            page = page + 1

        last_page_no = maximum
        page_no = 1
        while True:
            if page_no > last_page_no:
                break
            link = "http://www.nkorea.or.kr/board/index.html?id=coulmn&page=" + str(page_no)
            # print(link)
            yield scrapy.Request(link, callback = self.parse_each_pages, meta={'page_no': page_no, 'last_page_no': last_page_no})
            page_no += 1

    # function3: def parse_each_pages(self, response)
    # 페이지의 각 category 접근요청하는 함수
    def parse_each_pages(self, response):
        page_no = response.meta['page_no']
        last_page_no = response.meta['last_page_no']

        last = response.xpath('//*[@id="div_article_contents"]/tr[1]/td[1]/text()').get()
        if page_no == last_page_no:
            first = 1
        else:
            first = response.xpath('//*[@id="div_article_contents"]/tr[29]/td[1]/text()').get()

        category_last_no = int(last) - int(first)+1
        category_no = 1

        while 1:
        # 해당 url을  item에 넣어준다.
            if(category_no > category_last_no):
                break
            category_link = response.xpath('//*[@id="div_article_contents"]/tr[' + str(2*category_no-1) + ']/td[2]/font/a/@href').get()
            category_link = category_link.replace("./", "")
            url =  "http://www.nkorea.or.kr/board/" + category_link
            # print(url)
            date = response.xpath('//*[@id="div_article_contents"]/tr['+ str(2*category_no-1) +']/td[5]/text()').get()
            writer = response.xpath('//*[@id="div_article_contents"]/tr['+ str(2*category_no-1) +']/td[3]/text()').get()
 			# item 객체생성
            item = CrawlnkdbItem()
            item[config['VARS']['VAR4']] = date
            item[config['VARS']['VAR3']] = writer
 			# item url에 할당
            yield scrapy.Request(url, callback=self.parse_category, meta={'item':item})
            category_no += 1

    # * function4 각 항목마다 bodys, titles, writers, dates를 가져온다. def parse_category(self, response):
    def parse_category(self, response):
	# 각 항목마다 bodys, titles, writers, dates를 가져온다.
        title = response.css('.Form_left2::text').get()
        body =response.css('#tmp_content').xpath('string()').get()
        top_category = response.xpath('//*[@id="left_menu"]/p/span/text()').get()
        published_institution = "북한연구소"
        item = response.meta['item']
        item[config['VARS']['VAR1']] = title
        item[config['VARS']['VAR2']] = body
        item[config['VARS']['VAR5']] = published_institution
        item[config['VARS']['VAR6']]= "http://www.nkorea.or.kr/board/"
        item[config['VARS']['VAR7']] = top_category

        yield item
