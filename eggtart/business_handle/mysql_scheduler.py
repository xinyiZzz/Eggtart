# -*- coding: utf-8 -*-
'''
Name: MySQL业务调度
Author：XinYi/zmx 609610350@qq.com
Time：2015.9.3
'''

import sys
import os
import re
import time
import json
import traceback
import threading

sys.path.append('../server_base')
from errors import DependencyNotInstalledError
from utils import transfer_time_reformat, hash_md5, get_format_time, get_ip_location

try:
    import MySQLdb
except ImportError:
    raise DependencyNotInstalledError('MySQLdb')

from mysql_handle_base import MysqlHandleBase
from mysql_handle import engine_describe, url_list

reload(sys)
sys.setdefaultencoding('utf8')


class MysqlScheduler():

    '''
    定义任务具体执行操作
    '''

    def __init__(self, mysql_host='127.0.0.1', mysql_db='test',  mysql_user='root',  mysql_password='zxy'):
        self.mysql_handle_base = MysqlHandleBase(mysql_host, mysql_user,
                                                 mysql_password, mysql_db)
        self.engine_describe = engine_describe.get_engine_describe(
            self.mysql_handle_base)

    def task_operate(self, job_body):
        if job_body['cmd'] == 'ENGINE_TEST':
            url_list.into_url_list(self.mysql_handle_base, job_body)
            task_info.into_task_info(self.mysql_handle_base, job_body)
            task_engine_status.into_task_engine_status(self.mysql_handle_base, job_body)
            url_save_dir.into_url_save_dir(self.mysql_handle_base, job_body)
        return job_body
        

if __name__ == '__main__':
    mysql_handle = MysqlScheduler(mysql_host='127.0.0.1', mysql_db='test',  mysql_user='root',  mysql_password='zxy')
    job_body = open(
        '/home/Eggtart/engine_test_data/1469843362_37.json')
    job_body = json.load(job_body)
    test = MysqlScheduler()
    test.task_operate(job_body)
