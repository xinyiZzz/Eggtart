# -*- coding: utf-8 -*-
'''
Name: task_info 表操作方法
Author：XinYi 609610350@qq.com
Time：2015.9.3
'''

import sys
import os

present_path = os.path.abspath('.').split('/')[:-2]
sys.path.append('/'.join(present_path) + '/server_base')
from utils import get_format_time
from deco import add_table_feild
TableFieldDescripe = {'task_id': 's', 'task_name': 's', 'add_way': 's', 'task_engine': 's', 'error': 's','create_time': 's', 'url_list': 's', 'waiting_engine': 's', 'running_engine': 's', 'run_win_engine': 's', 'run_error_engine': 's', 'start_time': 's', 'stop_time': 's', 'run_time': 'd'}


def into_task_info(mysql_handle_base, job_body):
    '''
    填写task_info数据表
    '''
    table_field_descripe = TableFieldDescripe
    if 'run_time' in job_body:
        job_body['run_time'] = int(job_body['run_time'])
    update_fields = {'task_type': [job_body['cmd'], 's']}
    update_fields = add_table_feild(
        job_body, table_field_descripe, update_fields)
    # 引擎执行结果转换给字符串格式
    update_fields['waiting_engine'] = ['-'.join(update_fields['waiting_engine'][0]), 's']
    update_fields['running_engine'] = ['-'.join(update_fields['running_engine'][0]), 's']
    update_fields['run_win_engine'] = ['-'.join(update_fields['run_win_engine'][0]), 's']
    update_fields['run_error_engine'] = ['-'.join(update_fields['run_error_engine'][0]), 's']
    task_id = job_body['task_id']
    select_result = mysql_handle_base.select('task_info', fields=['task_id'], wheres={
        'task_id': [task_id, 's']}, fetch_type='one')
    if select_result == False:
        result = mysql_handle_base.insert('task_info', update_fields)
    else:
        if update_fields['task_engine'] != '':
            update_fields['task_state'] = ['01', 's']
        else:
            update_fields['task_state'] = ['02', 's']
        del update_fields['task_engine']
        wheres = {'task_id': [job_body['task_id'], 's']}
        result = mysql_handle_base.update(
            'task_info', update_fields, wheres)


def insert_task(mysql_handle_base, task_name='test', user_id=1, task_type=0, task_engine='',
                protected_id='', gray_id='', monitor_id='', counterfeit_id=''):
    '''
    创建任务
    '''
    fields = {'task_name': [task_name, 's'],
              'user_id': [user_id, 'd'],
              'task_type': [task_type, 'd'],
              'task_engine': [task_engine, 's'],
              'protected_id': [protected_id, 's'],
              'gray_id': [gray_id, 's'],
              'monitor_id': [monitor_id, 's'],
              'counterfeit_id': [counterfeit_id, 's'],
              'add_time': [get_format_time(), 's']}
    return mysql_handle_base.insert('task_info', fields, return_id=True)


def get_task(mysql_handle_base, task_id):
    '''
    从task_info表中读取指定任务的last_time
    '''
    table_name = 'task_info'
    fields = ['last_time', 'user_id', 'task_type', 'task_engine', 'protected_id',
              'gray_id', 'monitor_id', 'counterfeit_id', 'add_time']
    wheres = {'task_id': [task_id, 'd']}
    task_info = mysql_handle_base.select(
        table_name, fields, wheres, fetch_type='one')
    return task_info


if __name__ == '__main__':
    from mysql_handle_base import MysqlHandleBase
    mysql_handle = MysqlScheduler(mysql_host='127.0.0.1', mysql_db='test',  mysql_user='root',  mysql_password='zxy')
    task_id = insert_task(mysql_handle_base)[1]
    print task_id
    print get_task_last_time(mysql_handle_base, task_id)
