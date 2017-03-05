# -*- coding: utf-8 -*-
'''
Name: 操作方法装饰器
Author：XinYi 609610350@qq.com
Time：2015.9.3
'''

import sys
import os
from os.path import join as pjoin
import copy

present_path = os.path.abspath('.').split('/')[:-2]
sys.path.append('/'.join(present_path) + '/server_base')
from utils import hash_md5, get_format_time


def arg_exist(table_name):
    '''
    判断table_name表中的是否有匹配wheres中字段的记录
    '''
    def _deco(func):
        def __deco(mysql_handle_base, *args, **kwargs):
            wheres = func(mysql_handle_base, *args, **kwargs)
            return mysql_handle_base.select(
                table_name, ['*'], wheres, fetch_type='one')
        return __deco
    return _deco


def add_table_feild(entity, table_field_descripe, fields={}):
    '''
    把entity字典在table_field_descripe中出现的字段名，添加到fields中
    entity：{'task_id':'rewqr23421f'}
    table_field_descripe:{'task_id':'s'}
    fields:{task_id:['rewqr23421f', 's']}
    '''
    fields = copy.copy(fields)
    for field in entity:
        if field in table_field_descripe:
            fields[field] = [entity[field],
                             table_field_descripe[field]]
    return fields


def deco_insert_urls(table_name):
    '''
    将urls插入table_name表中
    '''
    def _deco(func):
        def __deco(mysql_handle_base, urls, add_way='test'):
            @arg_exist(table_name)
            def hash_exist(mysql_handle_base, url):
                wheres = {'url_hash': [hash_md5(url), 's']}
                return wheres
            fields = [('url_hash', 's'), ('url', 's'),
                      ('add_way', 's'), ('add_time', 's')]
            param = []
            for url in urls:
                if hash_exist(mysql_handle_base, url) is not False:  # 说明该URL已存在
                    continue
                param.append((hash_md5(url), url,
                              add_way, get_format_time()))
            if param == []:
                return False
            param = tuple(param)
            return mysql_handle_base.batch_insert(table_name, fields, param)
        return __deco
    return _deco


def count_resource_num(save_path):
    '''
    统计保存的网站的 images/目录下 js，css，pic(.jpg, .gif, .png), html_num 资源文件数
    '''
    img_num = 0
    js_num = 0
    css_num = 0
    html_num = 0
    file_name_list = os.listdir(save_path)
    for file_name in file_name_list:
        if file_name.find('.htm') != -1:
            html_num += 1
    html_num = html_num - 2
    image_path = pjoin(save_path, 'images')
    if os.path.exists(image_path):
        file_name_list = os.listdir(image_path)
        for file_name in file_name_list:
            if file_name.find('.css') != -1:
                css_num += 1
            elif file_name.find('.js') != -1:
                js_num += 1
            elif file_name.find('.jpg') != -1 or file_name.find('.gif') != -1 or file_name.find('.png') != -1:
                img_num += 1
    return js_num, css_num, img_num, html_num


def insert_dir_tree(table_name):
    '''
    在MySQL的xxx_dir_tree表中插入网页信息在本地的保存记录，即每个网页都保存了哪些信息
    timestamp_dir_path: 网页信息到时间戳目录的绝对路径
    file_list: 网页信息目录下第一层文件列表
    update_sign: 更新标志，为True时若记录已经存在则更新
    '''
    def _deco(func):
        def __deco(mysql_handle_base, url, timestamp_dir_path, file_list=[], update_sign=True):
            timestamp_abs_dir_clist = timestamp_dir_path.split('/')
            fields = {'url_hash': [hash_md5(url), 's'],
                      'timestamp': [timestamp_abs_dir_clist[-1], 's'],
                      'url': [url, 's'],
                      'update_time': [get_format_time(), 's'],
                      'save_path': ['/'.join(timestamp_abs_dir_clist[timestamp_abs_dir_clist.index('web_info')+1:]), 's'],
                      'url_file': [0, 'd'],
                      'main_html': [0, 'd'],
                      'normal_html_html': [0, 'd'],
                      'html': [0, 'd'],
                      'css': [0, 'd'],
                      'js': [0, 'd'],
                      'pic': [0, 'd'],
                      'text_json': [0, 'd'],
                      'block_json': [0, 'd'],
                      'border_json': [0, 'd'],
                      'block_html': [0, 'd'],
                      'cut_img': [0, 'd'],
                      'vips_imgs_txt': [0, 'd'],
                      'view_json': [0, 'd'],
                      'webpage_jpeg': [0, 'd'],
                      'blockpage_jpeg': [0, 'd'],
                      'other': ['', 's']
                      }
            for f in file_list:
                if f == 'images':  # 第二版网页保存引擎中images目录下存储资源
                    resource_nums = count_resource_num(timestamp_dir_path)
                    fields['js'][0] = resource_nums[0]
                    fields['css'][0] = resource_nums[1]
                    fields['pic'][0] = resource_nums[2]
                    fields['html'][0] = resource_nums[3]
                elif f in fields:  
                    #对文件名和fields中一致的文件或目录进行添加， 第一版网页保存引擎中各资源存储在fields中对应名称的目录下
                    if os.path.isdir(pjoin(timestamp_dir_path, f)):
                        f_num = len(os.listdir(pjoin(timestamp_dir_path, f)))
                        fields[f][0] = f_num
                    else:
                        fields[f][0] = 1
                elif f.replace('.', '_') in fields: # 对有后缀的文件进行添加
                    fields[f.replace('.', '_')][0] = 1
                else:
                    fields['other'][0] += (f + '/')
            wheres = {'url_hash': fields['url_hash'],
                      'timestamp': fields['timestamp']}
            if mysql_handle_base.select(table_name, ['*'], wheres):
                if update_sign:
                    mysql_handle_base.update(
                        table_name, fields, wheres)
            else:
                mysql_handle_base.insert(table_name, fields)
            return True
        return __deco
    return _deco


if __name__ == '__main__':
    once_select_result = {'protected_judge': 'fffff', 'protected_result': '11111111'}
    table_field_descripe = {'protected_judge': 'd', 'protected_result': 's',
                      'counterfeit_judge': 'd', 'counterfeit_result': 's', 'url': 's', 'url_hash': 's', 'engine_type': 's'}
    update_fields = add_table_feild(once_select_result, table_field_descripe)
    update_fields = add_table_feild(once_select_result, table_field_descripe, update_fields)
    update_fields = add_table_feild(once_select_result, table_field_descripe)