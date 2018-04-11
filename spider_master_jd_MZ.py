#coding=utf-8
import copy
import os
import sys
import time
from threading import Thread
from pymongo import DESCENDING as mongoDescending
from Config.Base import *
from JdComment import jd_mz_comment
from Models.Models import SpiderCommand
from MongoRelated.mongoConnection import *
from toollib.logger_jd_mz import Logger


#获取脚本文件的当前路径
def cur_file_dir():
     #获取脚本路径
     path = sys.path[0]

     if os.path.isdir(path):
         return path
     elif os.path.isfile(path):
         return os.path.dirname(path)

command_base ='python '+cur_file_dir()+'/%s %s %d %d %s %s %d'
# command_base ='python3.6 /Users/kevinlv/JD_spider2/%s %s %d %d %s %s %d'

def startingOneSpider(spiderModel, db):

    # command_string =command_base %tuple([spiderModel.python_name,
    #                                      spiderModel.log_collection_name,
    #                                      spiderModel.product_index,
    #                                      spiderModel.page_nummber,
    #                                      spiderModel.catalog_collection_name,
    #                                      spiderModel.target_collexction_name,
    #                                      spiderModel.maxPage_num_control])
    # Logger.debug(command_string)
    # os.system(command_string)
    try:
        jd_mz_comment.main(spiderModel.log_collection_name, spiderModel.product_index, spiderModel.page_nummber, spiderModel.catalog_collection_name, spiderModel.target_collexction_name, spiderModel.maxPage_num_control, db)
    except Exception as e:
        print(e)
        Logger.debug('重启')
        mongo_conn.close()
        time.sleep(60)


def monitoringOneSpider(spiderModel, db):

    # startingOneSpider(spiderModel)

    while 1:

        log_collection = db[spiderModel.log_collection_name]

        result_list =list(log_collection.find().sort('log_time', direction=mongoDescending).limit(5))
        if len(result_list)>0:
            last_log_dict =result_list[0]
            Logger.debug('log checking', last_log_dict)
            if last_log_dict['type'] =='跳出':

                df =pd.DataFrame(result_list)
                type_series = df['type'].value_counts()
                if type_series['跳出'] >= 4:   #跳过产品 继续
                    next_product_index =last_log_dict['product_index']+1
                    next_page_nummber =0
                else:
                    # 原产品跳页继续
                    next_product_index =last_log_dict['product_index']
                    next_page_nummber =last_log_dict['current_page']+1
                time.sleep(5)
                Logger.debug('restarting')

                new_spider = copy.deepcopy(spiderModel)
                new_spider.product_index =next_product_index
                new_spider.page_nummber =next_page_nummber

                startingOneSpider(new_spider, db)

            elif last_log_dict['type'] =='成功':

                now =time.time()
                last_time_stamp =last_log_dict['log_time']
                time_span =now-last_time_stamp
                Logger.debug(time_span)
                if time_span>30:
                    myPrint('last success,outtime,restarting')
                    next_product_index =last_log_dict['product_index']
                    next_page_nummber =last_log_dict['current_page']+1

                    new_spider = copy.deepcopy(spiderModel)
                    new_spider.product_index =next_product_index
                    new_spider.page_nummber =next_page_nummber
                    startingOneSpider(new_spider, db)

            elif last_log_dict['type'] == '已经存在':
                Logger.warning('exist, restarting')
                next_product_index =last_log_dict['product_index']+1
                next_page_nummber = 0
                new_spider = copy.deepcopy(spiderModel)
                new_spider.product_index = next_product_index
                new_spider.page_nummber = next_page_nummber

                startingOneSpider(new_spider, db)

            elif last_log_dict['type'] =='爬取完毕':
                Logger.warning('done, restarting')
                time.sleep(100)
                new_spider = copy.deepcopy(spiderModel)
                new_spider.product_index = 0
                new_spider.page_nummber = 0
                new_spider.maxPage_num_control = 50

                startingOneSpider(new_spider, db)

        else:
            startingOneSpider(spiderModel, db)
        mongo_conn.close()
        time.sleep(10)

if __name__ == '__main__':
    if isLocal:
        # 如果是本地数据库
        mongo_conn = connect_mongo(host=mongodb_host, port=mongodb_port, username=mongodb_username, password=mongodb_password, db=mongodb_db)
    else:
        # 链接阿里云数据库
        mongo_conn = connect_mongo(host=ALIYUN_HOST, port=ALIYUN_PORT, username=ALIYUN_USERNAME, password=ALIYUN_PASSWORD,db=ALIYUN_DB)

    db = mongo_conn[mongodb_db]
    # 取出HF_前缀的集合名称

    collection_name_list = COLLECTION_NAME_LIST_MZ


    for i in range(len(collection_name_list)):
        Logger.info(collection_name_list[i])

        spider = SpiderCommand()
        spider.log_collection_name = collection_name_list[i]+'_comment_log'
        spider.python_name = 'jd_mz_comment.py'
        spider.product_index = 0
        spider.page_nummber = 0
        spider.catalog_collection_name = collection_name_list[i]
        spider.target_collexction_name = collection_name_list[i]+'_comments'
        spider.maxPage_num_control = 100
        collection_name_list[i] = spider
    mongo_conn.close()

    proc_record = []
    for i in range(len(collection_name_list)):
        p = Thread(target=monitoringOneSpider, args=(collection_name_list[i], db,))
        p.start()
        proc_record.append(p)

    for thread in proc_record:
        thread.join()



