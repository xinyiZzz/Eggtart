#!/usr/bin/python
#-*-coding:utf-8-*-
'''
Name: web_info下哈希目录操作
Author：XinYi 609610350@qq.com
Time：2016.4

模块介绍：
    对web_info目录保存的网站信息进行相关操作
    提供接口如下：
    web_info_transfer: web_info中在两个*_web目录下进行网页信息的转移
'''

import os
import shutil
from os.path import join as pjoin
import json

from hash_path_builder import get_web_hash_path_abs, get_hash_dir_info
from utils import hash_md5, get_format_time

_PATH = '/'.join(os.path.abspath('.').split('/')
                 [:-2])  # _PATH 当前路径的上两级目录，即工程根目录


def path_file_transfer(source_path, target_path):
    '''
    将source_path路径下的所有目录及文件转移到target_path路径下
    '''
    if not os.path.exists(source_path):
        return False
    timestamp_dirs = os.listdir(source_path)
    for timestamp_dir in timestamp_dirs:
        source_web_timestamp_path = pjoin(source_path, timestamp_dir)
        target_web_timestamp_path = pjoin(target_path, timestamp_dir)
        try:
            if os.path.isdir(source_web_timestamp_path):
                shutil.copytree(source_web_timestamp_path,
                                target_web_timestamp_path)
            elif os.path.isfile(source_web_timestamp_path):
                shutil.copyfile(source_web_timestamp_path,
                                target_web_timestamp_path)
        except OSError:
            # 说明 target_web_timestamp_path 已经存在
            pass
    return True


def web_info_transfer(url, source_web_type, target_web_type):
    '''
    将网站url在source_web_type类型的web_info目录下保存的信息，复制到
    target_web_type类型的web_info目录下
    '''
    source_root_path = pjoin(_PATH, 'web_info/' + source_web_type + '_web')
    source_web_path = get_web_hash_path_abs(url, source_root_path, 4)
    target_root_path = pjoin(_PATH, 'web_info/' + target_web_type + '_web')
    target_file_path = get_web_hash_path_abs(url, target_root_path, 4)
    return path_file_transfer(source_web_path, target_file_path)


def search_web_info(source_web_type):
    '''
    搜索web_info目录下保存的网页信息中非规范化的数据
    '''
    file_list = get_hash_dir_info(
        pjoin(_PATH, 'web_info/' + source_web_type + '_web'), 4)
    true_file = ['css', 'js', 'pic', 'html', 'url_file', 'main.html']
    false_path = {}
    for url in file_list:
        for timestamp_dir in file_list[url]:
            list_after_filtering = [
                file_name for file_name in file_list[url][timestamp_dir] if file_name not in true_file]
            if list_after_filtering != []:
                if timestamp_dir not in false_path:
                    false_path[timestamp_dir] = list_after_filtering
                else:
                    false_path[timestamp_dir].append(list_after_filtering)
                '''
                for each_element in list_after_filtering:
                    os.remove(file_name + '/' + each_element)
                '''
    with open('false_path.json', 'w') as f:
        json.dump(false_path, f)


if __name__ == '__main__':
    search_web_info('complete_save_web')
    web_info_transfer(url, 'complete_save_web', 'signal_save_web')
