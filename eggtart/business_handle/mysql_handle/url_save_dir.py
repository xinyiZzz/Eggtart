# -*- coding: utf-8 -*-
'''
Name: url_save_dir 表操作方法
    存储网页信息在本地的保存记录，即每个网页都保存了哪些信息，
Author：XinYi 609610350@qq.com
Time：2015.9.3
'''

import sys
import os

present_path = os.path.abspath('.').split('/')[:-2]
sys.path.append('/'.join(present_path) + '/server_base')

from os.path import join as pjoin
from hash_path_builder import get_hash_dir_info
from utils import hash_md5, get_format_time
from deco import arg_exist, insert_dir_tree

# _PATH 当前工作路径的上一级目录
_PATH = '/'.join(present_path[:-1])


def get_url_save_dir_info(mysql_handle_base):
    '''
    获取数据库中全部仿冒网站的目录信息
    '''
    table_name = 'url_save_dir'
    fields = ['url', 'save_path', 'main_html']
    return mysql_handle_base.select(
        table_name, fields, fetch_type='all')


@arg_exist("url_save_dir")
def hash_exist(mysql_handle_base, url, timestamp_dir_path):
    '''
    判断一个记录是否在 url_save_dir 表中
    '''
    wheres = {'url_hash': [hash_md5(url), 's'],
              'timestamp': [timestamp_dir_path.split('/')[-1], 's']}
    return wheres


@insert_dir_tree("url_save_dir")
def insert_url_save_dir(mysql_handle_base, url, timestamp_dir_path, file_list, update_sign=True):
    '''
    插入网页保存的目录信息到 url_save_dir 表中
    timestamp_dir_path: 网页信息到时间戳目录的绝对路径
    file_list: 网页信息目录下第一层文件列表
    update_sign: 更新标志，为True时若记录已经存在则更新
    '''
    pass


def update_url_save_dir(mysql_handle_base, update_sign=True):
    '''
    更新web_info/complete_save_web目录所有信息到MySQL的 url_save_dir 表中
    hash_dir_info 例如：{URL:{时间戳路径:[文件列表]}, {时间戳路径:[文件列表]}, 'URL':[]}
    '''
    hash_dir_info = get_hash_dir_info(
        pjoin(_PATH, 'web_info/complete_save_web'), 1)
    for url in hash_dir_info:
        for timestamp_dir_path in hash_dir_info[url]:
            insert_gray_dir_tree(mysql_handle_base, url, timestamp_dir_path,
                                 hash_dir_info[url][timestamp_dir_path], update_sign)


def into_url_save_dir(mysql_handle_base, job_body):
    '''
    将任务结果插入 url_save_dir 数据表
    '''
    for once_task in job_body['task_list']:
        url = once_task['url']
        if 'path' in once_task:
            timestamp_dir_path = once_task['path']
            file_list = os.listdir(once_task['path'])
            insert_gray_dir_tree(mysql_handle_base, url,
                                 timestamp_dir_path, file_list)
            continue
        if 'web_save_resource_num' in once_task:
            web_save_resource_num = once_task['web_save_resource_num']
            timestamp_abs_dir_clist = timestamp_dir_path.split('/')
            update_fields = {'html': [int(web_save_resource_num['html_num']), 'd'], 'css': [int(web_save_resource_num[
                'css_num']), 'd'], 'js': [int(web_save_resource_num['js_num']), 'd'], 'pic': [int(web_save_resource_num['img_num']), 'd']}
            wheres = {'url_hash': [hash_md5(once_task['url']), 's'], 'timestamp': [
                timestamp_abs_dir_clist[-1], 's']}
            result = mysql_handle_base.update(
                'url_save_dir', update_fields, wheres)


if __name__ == '__main__':
    from mysql_handle_base import MysqlHandleBase
    mysql_handle = MysqlScheduler(mysql_host='127.0.0.1', mysql_db='test',  mysql_user='root',  mysql_password='zxy')
    print get_counterfeit_dir_info(mysql_handle_base)
    update_webinfo_dir_tree(mysql_handle_base)
