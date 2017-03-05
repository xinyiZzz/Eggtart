# -*- coding: utf-8 -*-
'''
Name: engine_describe表操作方法
Author：XinYi 609610350@qq.com
Time：2015.9.3
'''

import sys
import os

present_path = os.path.abspath('.').split('/')[:-2]
sys.path.append('/'.join(present_path) + '/server_base')


def get_engine_describe(mysql_handle_base):
    '''
    读取mysql的engine_describe表中对系统中所有引擎描述信息
    '''
    fields = ['engine_type', 'engine_code_name']
    get_result = mysql_handle_base.select(
        'engine_describe', fields, fetch_type='all')
    engine_describe = {}
    for engine_info in get_result:
        engine_describe[engine_info['engine_code_name']
                        ] = engine_info['engine_type']
    return engine_describe



if __name__ == '__main__':
    from mysql_handle_base import MysqlHandleBase
    mysql_handle = MysqlScheduler(mysql_host='127.0.0.1', mysql_db='test',  mysql_user='root',  mysql_password='zxy')
    print get_engine_describe(mysql_handle_base)
