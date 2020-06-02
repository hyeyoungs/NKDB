import os
import sys
import configparser
config = configparser.ConfigParser()
config.read('./../lib/config.cnf')

information_file = open("../final.txt", 'r')

while True:
    line = information_file.readline()
    if not line:
        break
    # here
    arr = line.split(',')
    #mongo_database = arr[0]
    #mongo_collection = arr[0]
    mongo_database = config['DB']['MONGO_DB']
    mongo_collection = "nkdb"
    execute_file_name = arr[1]
    os.chdir(config['SERVER']['PATH_SPIDER'])
    command = "scrapy crawl " + execute_file_name
    os.system(command)
    print("Finish following command: " + command)

information_file.close()
