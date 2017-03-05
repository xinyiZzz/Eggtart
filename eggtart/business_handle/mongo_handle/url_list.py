# -*- coding: utf-8 -*-
'''
Name: URL集合操作方法
Author：XinYi 609610350@qq.com
Time：2015.9.3
'''

import sys
import os
present_path = os.path.abspath('.').split('/')[:-2]
sys.path.append('/'.join(present_path) + '/server_base')
from utils import get_format_time
from mongo_handle_base import deal_mongo_error
from errors import DependencyNotInstalledError
from mongo_storage import UrlList

try:
    from mongoengine import DoesNotExist, ValidationError
except ImportError:
    raise DependencyNotInstalledError('mongoengine')

GRAY_MAX_URL_NUM = 10000  # 每个灰名单最大URL数量


@deal_mongo_error()
def create_url_list(mongo_handle_base, list_name='test', list_type='manual', usr_id=0, task_id=0):
    '''
    创建一个新的UrlList对象
    输入：列表名称、类型、用户id、任务id
    输出：UrlList对象，仅新创建记录，没有添加URL
    '''
    url_list = UrlList(list_num=0)
    url_list.creat_time = get_format_time()
    url_list.update_time = get_format_time()
    url_list.list_name = list_name
    url_list.list_type = list_type
    url_list.usr_id = int(usr_id)
    url_list.task_id = int(task_id)
    url_list.use_count = 0
    url_list.child_list = []
    url_list.save()
    return url_list


def divide_splist(l, s):
    '''
    将列表l平均分割为n个列表，每个列表s个元素
    '''
    return [l[i:i + s] for i in range(len(l)) if i % s == 0]


@deal_mongo_error()
def add_url_list(mongo_handle_base, add_list, objectID='', list_name='test',
                 list_type='manual', usr_id=0, task_id=0):
    '''
    储存一个URL列表到objectID指定的UrlList对象中，若不指定objectID则使用相关参数
    创建UrlList对象
    输入：objectID（已知document的objectID,若不指定则新创建）
          add_list（待添加URL列表）
    输出：添加urls的UrlList对象的objectID列表
    '''
    if add_list == []:
        return False
    elif isinstance(add_list, str) or isinstance(add_list, unicode):  # 说明仅传入一条URL
        add_list = [add_list]
    if objectID == '':
        url_list = create_url_list(
            mongo_handle_base, list_name, list_type, usr_id, task_id)
    else:
        url_list = getattr(UrlList, 'objects').get(id=objectID)
    # latest_url_list表示该url_list的最后一个子列表，若没有子列表则为当前列表
    if url_list.child_list != []:
        latest_url_list = getattr(UrlList, 'objects').get(
            id=url_list.child_list[-1])
    else:
        latest_url_list = url_list
    # 表示最后一个子列表还剩余多少url存储空间
    retain_url_num = GRAY_MAX_URL_NUM - latest_url_list.list_num
    if len(add_list) < retain_url_num:
        latest_url_list.urls.extend(add_list)
        latest_url_list.save()
        return [str(latest_url_list.id)]
    else:
        return_url_list_id = [str(latest_url_list.id)]
        latest_url_list.urls.extend(add_list[:retain_url_num])
        latest_url_list.save()
        div_add_list = divide_splist(
            add_list[retain_url_num:], GRAY_MAX_URL_NUM)
        for full_url_list in div_add_list:
            latest_url_list = UrlList(
                list_num=GRAY_MAX_URL_NUM, urls=full_url_list)
            latest_url_list.save()
            url_list.list_num += latest_url_list.list_num
            url_list.child_list.append(latest_url_list.id)
            return_url_list_id.append(str(latest_url_list.id))
        url_list.save()
        return return_url_list_id
    

@deal_mongo_error()
def expand_url_list(mongo_handle_base, objectID):
    '''
    对objectID进行拓展，将该UrlList对象的child_id子名单的objectID，
    连同输入objectID一起返回
    '''
    expand_objectID_list = []
    try:
        url_list = getattr(UrlList, 'objects').get(id=objectID)
    except (DoesNotExist, ValidationError), e:
        return False
    expand_objectID_list.append(str(url_list.id))
    for child_id in url_list.child_list:
        expand_objectID_list.append(str(child_id))
    return expand_objectID_list
    


def expand_url_lists(mongo_handle_base, objectID_list):
    '''
    对objectID_list中每个objectID进行拓展，
    将每个UrlList对象的child_id子名单的objectID，连同输入objectID一起返回
    '''
    expand_objectID_list = []
    for objectID in objectID_list:
        expand_objectID_list.extend(
            expand_url_list(mongo_handle_base, objectID))
    # 对expand_objectID_list去重并按原顺序返回
    func = lambda x, y: x if y in x else x + [y]
    expand_objectID_list = reduce(func, [[], ] + expand_objectID_list)
    return expand_objectID_list


@deal_mongo_error()
def get_url_list_num(mongo_handle_base, objectID):
    '''
    获取一个UrlList对象中usr的个数，包含其子列表child_list中url个数
    '''
    try:
        url_list = getattr(UrlList, 'objects').get(id=objectID)
    except (DoesNotExist, ValidationError), e:
        return False
    return url_list.list_num
    

@deal_mongo_error()
def get_url_list(mongo_handle_base, objectID, read_objectID=None, read_url=None):
    '''
    用迭代器，依次返回objectID对应的UrlList对象中URL和其child_list中对应的URL
    并可从read_objectID，read_url的位置之后继续读取，read_objectID可能为该objectID
    的child_list中的UrlList对象，则从该UrlList对象的read_url位置开始读取
    输入：待读取的objectID、之前在该objectID对应UrlList中读取间断的read_objectID和read_url
    输出：url_list迭代器
    '''
    objectID_list = expand_url_list(mongo_handle_base, objectID)
    if read_objectID is not None and read_objectID in objectID_list:
        objectID_list = objectID_list[objectID_list.index(read_objectID):]
    for objectID in objectID_list:
        try:
            url_list = getattr(UrlList, 'objects').get(id=objectID)
        except (DoesNotExist, ValidationError), e:
            raise StopIteration
        if objectID == read_objectID and read_url is not None and read_url in url_list.urls:
            url_site = url_list.urls.index(read_url)
            urls = url_list.urls[url_site + 1:]
        else:
            urls = url_list.urls
        for url in urls:
            yield url


if __name__ == '__main__':
    from mongo_handle_base import MongoHandleBase
    mongo_handle_base = MongoHandleBase(mongo_db='mongo_test', mongo_host='127.0.0.1',
                                        mongo_port=27017, mongo_username='root', mongo_password='')

    GRAY_MAX_URL_NUM = 3
    add_list = ['http://befxz.cc/',
                'http://bxtezp.cc/',
                'http://bxzyka.cc/',
                'http://bxzykm.cc/',
                'http://bzna7.cc/',
                'http://bzxcf.cc/',
                'http://ccktmp.cc/',
                'http://ccmfe.cc/',
                'http://coptx.cc/',
                'http://cpuzt.cc/',
                'http://curxzw.cc/',
                'http://www.jipiaochina.net/',
                'http://ytxrz.cc/',
                'http://yyzeus.cc/']
    objectID = add_url_list(mongo_handle_base, add_list=add_list, objectID='', list_name='test',
                            list_type='manual', usr_id=0, task_id=0)
    print objectID
    print expand_url_list(mongo_handle_base, objectID[0])
    print expand_url_lists(mongo_handle_base, [objectID[0], objectID[1]])
    print get_url_list_num(mongo_handle_base, objectID[0])
    print get_url_list_num(mongo_handle_base, objectID[1])
    print '*************************'
    get_urls_iter = get_url_list(mongo_handle_base, objectID[0])
    while 1:
        try:
            url = get_urls_iter.next()
            print url
        except StopIteration:
            break
    print '*************************'
    get_urls = []
    for url in get_url_list(mongo_handle_base, objectID[0], read_objectID=objectID[1], read_url='http://bzxcf.cc/'):
        get_urls.append(url)
    print get_urls
    print '*************************'
    print list(set(add_list).difference(set(get_urls)))
