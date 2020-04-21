# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
import configparser
config = configparser.ConfigParser()
config.read('./../lib/config.cnf')


import scrapy
class CrawlnkdbItem(scrapy.Item):
    # define the fields for your item here like:
    exec("%s = scrapy.Field()" % (config['VARS']['VAR1']))
    exec("%s = scrapy.Field()" % (config['VARS']['VAR2']))
    exec("%s = scrapy.Field()" % (config['VARS']['VAR3']))
    exec("%s = scrapy.Field()" % (config['VARS']['VAR4']))
    exec("%s = scrapy.Field()" % (config['VARS']['VAR5']))
    exec("%s = scrapy.Field()" % (config['VARS']['VAR6']))
    exec("%s = scrapy.Field()" % (config['VARS']['VAR7']))

    # when existing attachments
    exec("%s = scrapy.Field()" % (config['VARS']['VAR8']))
    exec("%s = scrapy.Field()" % (config['VARS']['VAR9']))
    exec("%s = scrapy.Field()" % (config['VARS']['VAR10']))
    exec("%s = scrapy.Field()" % (config['VARS']['VAR11']))
    exec("%s = scrapy.Field()" % (config['VARS']['VAR12']))
