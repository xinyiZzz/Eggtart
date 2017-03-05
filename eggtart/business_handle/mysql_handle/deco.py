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


if __name__ == '__main__':
    once_select_result = {'protected_judge': 'fffff', 'protected_result': '11111111'}
    table_field_descripe = {'protected_judge': 'd', 'protected_result': 's',
                      'counterfeit_judge': 'd', 'counterfeit_result': 's', 'url': 's', 'url_hash': 's', 'engine_type': 's'}
    update_fields = add_table_feild(once_select_result, table_field_descripe)
    update_fields = add_table_feild(once_select_result, table_field_descripe, update_fields)
    update_fields = add_table_feild(once_select_result, table_field_descripe)