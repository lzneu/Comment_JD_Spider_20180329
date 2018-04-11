# -*- coding: UTF-8 -*-
import pandas as pd
import pymysql
from pymongo import MongoClient, ASCENDING
from Config.config import *

# from pymongo import Connection
# import tkinter
''''连接mongodb, 返回mongodb的connnection
'''''


def connect_mongo(host, port, username, password, db):
    """ A util for making a connection to mongo """

    if isLocal:
        if username and password:
            # print('mongo username')
            mongo_uri = 'mongodb://%s:%s@%s:%s/%s' % (username, password, host, port, db)
            conn = MongoClient(mongo_uri)
        else:
            # print('mongo no username')
            conn = MongoClient(host, port)
    else:
        # 获取mongoclient
        conn = MongoClient([ALIYUN_MONGO_CONN_ADDR1, ALIYUN_MONGO_CONN_ADDR2], replicaSet=ALIYUN_MONGO_REPLICAT_SET)
        if username and password:
            # 授权. 这里的user基于admin数据库授权
            conn.power.authenticate(username, password)

    return conn


def read_mongo(db, collection, query, username=None, password=None, no_id=True):
    """ Read from Mongo and Store into DataFrame """
    from pymongo import DESCENDING as mongoDescending
    from pymongo import ASCENDING as mongoAscending
    # Connect to MongoDB
    # conn = connect_mongo(host=mongodb_host, port=mongodb_port, username=mongodb_username, password=mongodb_password,
    #                      db=db)
    # dataBase = conn[db]
    # Make a query to the specific DB and Collection.sort({"creationTime":1}
    cursor = db[collection].find(query).sort('_id', direction=ASCENDING)

    df = pd.DataFrame(list(cursor))
    # print(df)
    if (len(list(cursor)) > 0):  # 数据量为0 返回 Empty DataFrame
        # Expand the cursor and construct the DataFrame
        for i in range(0, len(df.columns)):
            pass
            # print ('kslsk', df.columns[i] ,i)
            # Delete the _id
            # if no_id:
            #     # print('删除')
            #     del df['_id']

    cursor.close()
    return df




def getDataDataFrameFromMysql(isLocal, category_type_id):
    """ A util for making a connection to mongo """
    category_type = int(category_type_id.split('#')[0])
    category_id = int(category_type_id.split('#')[1])
    store_id = int(category_type_id.split('#')[2])


    shop_id_list = []
    original_id_list = []
    name_list= []
    category_list = []
    brand_id_list = []
    shop_type_list = []
    category_id_list = []

    if isLocal:
        # 打开数据库连接
        db = pymysql.connect(mysql_host, mysql_username, mysql_password, mysql_db, charset='utf8')
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # SQL 查询语句
        sql = "SELECT * FROM PRODUCTS \
       WHERE (CATEGORY_TYPE = '%d' AND CATEGORY_ID = '%d' AND STORE_ID = '%d')" % (category_type, category_id, store_id)
        try:
            # 执行SQL语句
            cursor.execute(sql)
            # 获取所有记录列表
            results = cursor.fetchall()
            for row in results:
                shop_id = row['shop_id']
                original_id = row['original_id']
                name = row['name']
                brand_id = row['brand_id']
                shop_type = row['shop_type']
                category = category_type_id
                category_id = row['category_id']

                shop_id_list.append(shop_id)
                original_id_list.append(original_id)
                name_list.append(name)
                category_list.append(category)
                brand_id_list.append(brand_id)
                shop_type_list.append(shop_type)
                category_id_list.append(category_id)

        except Exception as e:
            print(e)

        # 关闭数据库连接
        db.close()

    else:
        # 打开数据库连接
        db = pymysql.connect(ALIYUN_MYSQL_HOST, ALIYUN_MYSQL_USERNAME, ALIYUN_MYSQL_PASSWORD, ALIYUN_MYSQL_DB, charset='utf8')
        cursor = db.cursor(pymysql.cursors.DictCursor)

        # SQL 查询语句
        sql = "SELECT * FROM PRODUCTS \
        WHERE (CATEGORY_TYPE = '%d' AND CATEGORY_ID = '%d' AND STORE_ID = '%d')" % (
        category_type, category_id, store_id)
        try:
            # 执行SQL语句
            cursor.execute(sql)
            # 获取所有记录列表
            results = cursor.fetchall()
            for row in results:
                shop_id = row['shop_id']
                original_id = row['original_id']
                name = row['name']
                brand_id = row['brand_id']
                shop_type = row['shop_type']
                category = category_type_id
                category_id = row['category_id']

                shop_id_list.append(shop_id)
                original_id_list.append(original_id)
                name_list.append(name)
                category_list.append(category)
                brand_id_list.append(brand_id)
                shop_type_list.append(shop_type)
                category_id_list.append(category_id)


        except Exception as e:
            print(e)

        # 关闭数据库连接
        db.close()
        # conn = MongoClient([ALIYUN_MONGO_CONN_ADDR1, ALIYUN_MONGO_CONN_ADDR2], replicaSet=ALIYUN_MONGO_REPLICAT_SET)
        # if username and password:
        #     # 授权. 这里的user基于admin数据库授权
        #     conn.power.authenticate(username, password)
        # 写到dataframe里面
    df = pd.DataFrame(
        {'shop_id': shop_id_list, 'original_id': original_id_list, 'name': name_list, 'category': category_list,
         'brand_id': brand_id_list, 'shop_type': shop_type_list, 'category_id': category_id_list})

    return df

"""
产品sql表中，有一个category_type时表示该产品属于某个大类对应关系为:
    1-洗涤类 2-洗护发 3-护肤类 4-美妆类 5-母婴类 6-口腔护理类 7-家用电器类
    sql备注里边也有
"""