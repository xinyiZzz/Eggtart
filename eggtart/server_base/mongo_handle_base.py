#!/usr/bin/env python
# coding: utf-8
'''
name: MongoDB操作基类，基于mongoengine库
Author：XinYi 609610350@qq.com
Time: 2015.9.3
'''

import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s-[%(asctime)s][%(module)s][%(funcName)s][%(lineno)d]: %(message)s')

import time
import traceback
from mongoengine import connect, errors


class MongoError(Exception):  # 数据库存储错误

    def __init__(self, dep):
        self.dep = dep

    def __str__(self):
        try:
            return "Mongo Error %d: %s" % (self.dep.args[0], self.dep.args[1])
        except IndexError:
            return "%s  Mongo Error %s" % (time.ctime(), self.dep.args)


def deal_mongo_error():
    '''
    focus deal Mongo error, print error info
    处理Mongo错误，打印出错的参数
    '''
    def _deco(func):
        def __deco(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except errors, e:
                logger.error('%s, *args: %s, **kwargs: %s' %
                             (MongoError(e), args, kwargs))
                traceback.print_exc()
                return False
        return __deco
    return _deco


class MongoHandleBase(object):

    '''
    MongoDB操作基类，基于mongoengine库
    '''

    def __init__(self, mongo_db='test', mongo_host='127.0.0.1',
                 mongo_port=27017, mongo_username='root', mongo_password=''):
        self.connect_Mongo(mongo_db, mongo_host, mongo_port,
                           mongo_username, mongo_password)

    @deal_mongo_error()
    def connect_Mongo(self, mongo_db, mongo_host, mongo_port, mongo_username, mongo_password):
        '''
        连接数据库
        '''
        connect(mongo_db, host=mongo_host, port=mongo_port,
                username=mongo_username, password=mongo_password)
        logging.info('connect mongo win, ip: %s' % mongo_host)

    def __del__(self):
        '''
        断开连接
        '''
        pass

    @deal_mongo_error()
    def del_document(self, documents):
        '''
        删除指定documents，可为单个object或object列表
        '''
        documents.delete()
        return True


if __name__ == "__main__":
    mongo_handle_base = MongoHandleBase(mongo_db='test', mongo_host='172.0.0.1',
                                        mongo_port=27017, mongo_username='root', mongo_password='')
