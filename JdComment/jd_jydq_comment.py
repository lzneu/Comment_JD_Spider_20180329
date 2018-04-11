# coding=UTF-8
import requests
import json
import random
import os, sys
from MongoRelated.mongoConnection import *
from Config.Base import *
from toollib.logger_jd_jydq import Logger

# from importlib import reload
# import sys
# reload(sys)
# sys.setdefaultencoding('utf-8')


user_proxy = True
ips = []
web_json_url = 'https://club.jd.com/comment/skuProductPageComments.action?productId=%s&score=0&sortType=6&page=%d&pageSize=10'  # 京东商品评论的json页面，第一个%s参数为商品id，第二个%d参数为评论的页数
comments = set()


def get_max_page_num(pid):
    page_url = web_json_url % (pid, 0)
    headers1 = {'GET': '',
                'Host': "club.jd.com",
                'User-Agent': "Mozilla/5.0 (Windows NT 6.2; rv:29.0) Gecko/20100101 Firefox/29.0",
                'Referer': 'http://item.jd.com/%s.html' % (pid)}
    Logger.info(page_url)

    response = requests.request(method='GET', url=page_url, headers=headers1)
    page_data = response.content.decode('gbk', 'ignore')

    page_dict = json.loads(page_data)
    return int(page_dict['maxPage'])


def get_comments(product_dic, commentID_list, pid, ptitle, item_catagory, page_num, mongo_collection, proxiesIP,
                 indexCollection):  # 爬取商品id为pid的商品的第page_num页的评论
    headers1 = {'GET': '',
                'Host': "club.jd.com",
                'User-Agent': "Mozilla/5.0 (Windows NT 6.2; rv:29.0) Gecko/20100101 Firefox/29.0",
                'Referer': 'http://item.jd.com/%s.html' % (pid)}
    Logger.info(page_num)

    page_url = web_json_url % (pid, page_num)
    # req = urllib2.Request(url = page_url, headers = headers1)
    Logger.info(page_url)

    try:
        response = requests.request(method='GET', url=page_url, headers=headers1)
        # session =requests.session()
        # session.get(url=page_url,)
    except (Exception):
        # myPrint(e)
        successtag = False
        # i+=1
        # myPrint(Exception)
        Logger.info('ccc  跳过')
        # import os
        os.system('say "attention please,  your program has Exception  "')
        # response=None
        return 'Empty'

    try:
        # page_data = urllib2.urlopen(req, timeout = 10).read()
        html_content = response.content.decode('gbk', 'ignore')
        page_dict = json.loads(html_content)
        # myPrint(page_dict)
        # raise
        comments = page_dict['comments']
        successtag = True
        myPrint(pid, len(comments))
    except(Exception):
        successtag = False
        # i+=1
        # myPrint('ccc  跳过')
        # os.system('say "attention please,  your program has Exception  "')
        return 'Empty'

    try:
        contents111 = []
        for comment in comments:
            # contents.append(comment['content'])
            # myPrint(comment)
            commentDict = {}
            content = deleteEscapeCharacter(comment['content'])
            # myPrint(content)

            created_at = comment['creationTime']
            userLevelName = comment['userLevelName']
            isMobile = comment['isMobile']
            score = comment['score']
            comment_id = comment['id']
            product_id = comment['referenceId']
            if product_id == '':
                raise

            # myPrint(creationTime,userLevelName,isMobile)
            tagsList = []
            if 'commentTags' in comment.keys():
                commentTags = comment['commentTags']

                # myPrint('ccc', commentTags)
                for commenTag in commentTags:
                    tagsList.append(commenTag['name'])
                    # myPrint(commenTag['name'])
            commentDict['comment_id'] = comment_id
            commentDict['product_id'] = str(product_id)
            commentDict['content'] = content
            commentDict['userLevelName'] = userLevelName
            commentDict['commentTags'] = tagsList
            commentDict['created_at'] = created_at

            if isMobile == True:
                commentDict['platform'] = 1
            elif isMobile == False:
                commentDict['platform'] = 2
            else:
                commentDict['platform'] = 0

            commentDict['score'] = score
            commentDict['product_title'] = ptitle
            commentDict['category'] = item_catagory
            commentDict['store_id'] = 1
            commentDict['brand_id'] = product_dic['brand_id']
            commentDict['category_id'] = product_dic['category_id']
            commentDict['shop_type'] = product_dic['shop_type']

            if commentDict['product_id'] == pid:
                insert_reslut = insertToMongo(commentID_list, mongo_collection, commentDict, indexCollection)
                contents111.append(insert_reslut)
    except Exception:
        Logger.info('ccc  跳过')
        # import os
        os.system('say "attention please,  your program has Exception  "')
        # response=None
        return 'Empty'

    Logger.info(contents111)
    return contents111


def scraw_web_json(product_collection, commentID_list, pid, ptitle, item_catagory, file_name, mongo_collection, proxiesIP, stnum,
                   maxPage_num_control, log_collection, indexCollection):
    # 获取该商品信息
    product_dic = list(product_collection.find({'original_id': pid}))[0]
    max_page_num = int(round(get_max_page_num(pid), 0))
    Logger.info('max_page_num =' + str(max_page_num))
    content_set = set()

    # max_page_num = 151
    if max_page_num >= 100:
        max_page_num = maxPage_num_control

    cunzai_count = 0
    for page_num2 in range(int(stnum), max_page_num):
        # if page_num%1==0:
        Logger.info('page_num:' + str(page_num2) + 'total' + str(max_page_num) + 'pid =' + str(pid))
        contents = get_comments(product_dic, commentID_list, pid, ptitle, item_catagory, page_num2, mongo_collection, proxiesIP,
                                indexCollection)
        Logger.info('product Index' + str(file_name))
        Logger.info(comments)

        if contents != 'Empty' and len(contents) > 0:
            log_dict = {'type': '成功', 'product_index': file_name, 'current_page': page_num2, 'log_time': time.time(),
                        'product_id': pid}
            log_collection.insert(log_dict)
            Logger.info('Sum =' + str(sum(contents)))

            if sum(contents) >= 10:
                # a = sum(contents)
                # print(a)
                log_dict = {'type': '已经存在', 'product_index': file_name, 'current_page': page_num2,
                            'log_time': time.time(), 'product_id': pid}
                log_collection.insert(log_dict)
                cunzai_count += 1

                if cunzai_count >= 3:
                    raise
            else:
                cunzai_count = 0

        if contents == 'Empty':
            log_dict = {'type': '跳出', 'product_index': file_name, 'current_page': page_num2, 'log_time': time.time(),
                        'product_id': pid}
            log_collection.insert(log_dict)
            # os.system('say "attention please,  your program has Exception  "')
            raise

        time.sleep(random.randint(5, 10) / 2)  # 休眠片刻


def deleteEscapeCharacter(sourceStr):
    temp = str(sourceStr).strip('\b')
    esCharList = ['\\', '\a', '\b', '\f', '\n', '\r', '\t', '\v', '&hellip']
    for esChar in esCharList:
        temp1 = temp.replace(esChar, '')
        temp = temp1

    return temp


from TimeClass.timeClass import *


def insertToMongo(commentID_list, mongo_collection, oneDict, indexCollection):
    if oneDict['comment_id'] not in commentID_list:
        # myPrint('aaa')
        timeStr = oneDict['created_at']  # 时间转换
        oneDict['created_at'] = convertTimeStringToDateTime(timeStr)
        Logger.info(oneDict['created_at'])
        mongo_collection.insert(oneDict)
        # 更新commentID_list
        commentID_list.append(oneDict['comment_id'])
        updateCommentID_list(oneDict['product_id'], commentID_list, indexCollection)
        return 0
    else:
        # myPrint(oneDict['commentID'],'已存在')
        # 已经存在该评论，不进行操作，直接返回1
        return 1


# def insertToMongo1(mongo_collection, oneDict, pid):
#     cursor = mongo_collection.find({'commentID': oneDict['commentID'], 'product_id': oneDict['product_id']}).limit(1)
#     # myPrint(oneDict['creationTime'])
#     # res =list(cursor)
#     # myPrint(res)
#     if len(list(cursor)) == 0:
#         # myPrint('aaa')
#         timeStr = oneDict['creationTime']  # 时间转换
#         oneDict['creationTime'] = convertTimeStringToDateTime(timeStr)
#         Logger.info(oneDict['creationTime'])
#         oneDict['pid'] = pid
#         res = mongo_collection.insert(oneDict)
#         # myPrint(res)
#         cursor.close()
#         return 0
#     else:
#         # myPrint(oneDict['commentID'],'已存在')
#         cursor.close()
#         return 1


''''重启脚本
'''''


def restart_program():
    python = sys.executable
    os.execl(python, python, *sys.argv)


def get_commentID_list(item_id, indexCollection):
    cursor = indexCollection.find({'productID': item_id})
    res = list(cursor)
    if len(res) != 0:
        commentID_list = res[0]['commentID_list']
    else:
        commentID_list = []
    cursor.close()
    return commentID_list


def updateCommentID_list(item_id, commentID_list, indexCollection):
    cursor = indexCollection.find({'productID': item_id})
    if len(list(cursor)) != 0:
        indexCollection.update({'productID': item_id}, {'$set': {'commentID_list': commentID_list}})
    else:
        indexCollection.insert({'productID': item_id, 'commentID_list': commentID_list})
    cursor.close()


def main(log_collection_name, product_index, page_nummber, catalog_collection_name, target_collexction_name,
         maxPage_num_control, db):
    Test = False
    if (not Test):
        # if len(sys.argv)>2:
        #     log_collection_name =sys.argv[1]
        #     product_index =int(sys.argv[2])
        #     startNum =int(sys.argv[3])
        #     catalog_collection_name =sys.argv[4]
        #     target_collexction_name =sys.argv[5]
        #     maxPage_num_control =int(sys.argv[6])
        log_collection_name = log_collection_name
        product_index = int(product_index)
        startNum = page_nummber
        catalog_collection_name = catalog_collection_name
        target_collexction_name = target_collexction_name
        maxPage_num_control = int(maxPage_num_control)

    log_collection = db[log_collection_name]
    catalog_df = read_mongo(db, catalog_collection_name, {'status': {"$in": [0, 1]}})
    item_id_list = catalog_df['original_id'].values

    item_title_list = catalog_df['name'].values
    catalog_list = catalog_df['category'].values

    collection = db[target_collexction_name]  # collection
    # 产品集合
    product_collection = db[target_collexction_name.replace('_comments', '')]

    # 索引集合，用来判重，每个product_id对应一个document ，其中有一个field 是commentID列表
    indexCollection = db['s_index_' + target_collexction_name.replace('s_', '')]

    # 上次中断的部分
    # product_index =1
    bottom_index = len(item_id_list) - 1

    if product_index <= bottom_index:
        item_id = str(item_id_list[product_index])

        item_title = item_title_list[product_index]

        item_catagory = catalog_list[product_index]

        # 获得该产品的commentID列表， 用于判重
        commentID_list = get_commentID_list(item_id, indexCollection)

        scraw_web_json(product_collection, commentID_list, item_id, item_title, item_catagory, product_index, collection, '', startNum,
                       maxPage_num_control,
                       log_collection, indexCollection)

    elif product_index > bottom_index:

        log_dict = {'type': '爬取完毕', 'product_index': bottom_index, 'current_page': 99, 'log_time': time.time()}
        log_collection.insert(log_dict)
        raise

    if product_index == bottom_index:
        log_dict = {'type': '爬取完毕', 'product_index': bottom_index, 'current_page': 99, 'log_time': time.time()}
        log_collection.insert(log_dict)
        raise

    for i in range(product_index + 1, len(catalog_df)):
        # for item_id in item_id_lis:

        temp = str(item_id_list[i])
        item_id = temp

        item_title = item_title_list[i]

        item_catagory = catalog_list[i]

        # item_store_type = store_type_list[i]

        # spider_start_date = spider_start_date_list[i]
        # item_id ='1545858'
        proxiesIP = ''
        startNum = 0
        commentID_list = get_commentID_list(item_id, indexCollection)
        scraw_web_json(product_collection, commentID_list, item_id, item_title, item_catagory, i, collection, proxiesIP, startNum,
                       maxPage_num_control, log_collection, indexCollection)


    if i == (len(catalog_df) - 1):
        log_dict = {'type': '爬取完毕', 'product_index': i, 'current_page': 99, 'log_time': time.time()}
        log_collection.insert(log_dict)
        raise
