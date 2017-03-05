# -*- coding: utf-8 -*-
'''
Name: url_list表操作方法
Author：XinYi 609610350@qq.com
Time：2015.9.3
'''

import sys
import os

present_path = os.path.abspath('.').split('/')[:-2]
sys.path.append('/'.join(present_path) + '/server_base')
from utils import hash_md5, get_format_time, get_ip_location
from deco import arg_exist, deco_insert_urls, add_table_feild
import engine_describe

TableFieldDescripe = {'url_hash': 's', 'url': 's', 'ip': 's', 'add_time': 's', 'add_way': 's', 'task_id': 's', 'waiting_engine': 's', 'running_engine': 's', 'run_win_engine': 's', 'run_error_engine': 's'}


@arg_exist("url_list")
def hash_exist(mysql_handle_base, url):
    '''
    判断一个url是否在url_list表中
    '''
    wheres = {'url_hash': [hash_md5(url), 's']}
    return wheres


@deco_insert_urls("url_list")
def insert_urls(mysql_handle_base, urls, add_way='test'):
    '''
    将urls添加到mysql的url_list中
    '''
    pass


def into_url_list(mysql_handle_base, job_body):
    '''
    将任务结果在url_list数据表中插入一条记录存储
    '''
    engine_describe_all = engine_describe.get_engine_describe(
        mysql_handle_base)
    # 向数据表中填写task_list中相关数据
    table_field_descripe = TableFieldDescripe
    insert_urls(mysql_handle_base, job_body['url_list'], job_body['add_way'])
    update_fields = add_table_feild(job_body, table_field_descripe)
    # 防止下面添加add_way时重复
    if 'add_way' in update_fields:
        del update_fields['add_way']
    for once_task in job_body['task_list']:
        update_fields = add_table_feild(
            once_task, table_field_descripe, update_fields)
        # 防止下面添加url时重复
        if 'url' in update_fields:
            del update_fields['url']
        run_win_engine_list = []
        run_error_engine_list = []
        # 分别把操作成功的引擎和操作失败的引擎添加到相应列表中(此处失败分为对网页分析失败和引擎启动失败两部分)
        # 对网页分析失败部分
        for field, value in once_task.iteritems():
            if field.find('_status') != -1:
                engine_code_name = field[0:field.find('_status')]
                engine_type = engine_describe_all[engine_code_name]
                if value == True:
                    run_win_engine_list.append(engine_type)
                elif value == False:
                    run_error_engine_list.append(engine_type)
        # 引擎启动失败部分
        run_error_engine_list.extend(job_body['run_error_engine'])
        # 引擎执行结果转换给字符串格式
        update_fields['run_win_engine'] = ['-'.join(run_win_engine_list), 's']
        update_fields['run_error_engine'] = ['-'.join(run_error_engine_list), 's']
        update_fields['waiting_engine'] = ['-'.join(update_fields['waiting_engine'][0]), 's']
        update_fields['running_engine'] = ['-'.join(update_fields['running_engine'][0]), 's']
        # 获取指令url的ip
        ip_location = get_ip_location(once_task['url'])
        update_fields = add_table_feild(
            ip_location, table_field_descripe, update_fields)
        wheres = {'url_hash': [hash_md5(once_task['url']), 's']}
        result = mysql_handle_base.update(
            'url_list', update_fields, wheres)


if __name__ == '__main__':
    from mysql_handle_base import MysqlHandleBase
    mysql_handle = MysqlScheduler(mysql_host='127.0.0.1', mysql_db='test',  mysql_user='root',  mysql_password='zxy')
    copy_gray_list(mysql_handle_base, 'https://www.baidu.com')
    '''
    urls = ['http://www.baidu.com/',
            'http://www.icbc.com.cn/',
            'http://www.taobao.com/']
    print insert_urls(mysql_handle_base, urls)
    print hash_exist(mysql_handle_base, 'http://www.baidu.com/')
    # print undate_gray_check_result_new(mysql_handle_base,
    # 'http://curxzw.cc/', 'title', 2, {'fad': 1})
    '''
