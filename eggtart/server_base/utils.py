#!/usr/bin/python
#-*-coding:utf-8-*-
'''
Name: 小工具
Author：XinYi 609610350@qq.com
2015.10.3
'''

import hashlib
import os
import socket
import fcntl
import struct
from socket import gethostbyname
import shutil
import sys
import time
import traceback
import ip2loc
import yaml
import logging
import logging.config
import cloghandler
from os.path import join as pjoin


def get_format_time():
    '''
    生成格式化当前时间, 例如: 2016-04-01_22-40-52
    '''
    return time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime(time.time()))


def getLocalIp(ifname="eth0"):
    '''
    获得本机IP
    '''
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(sock.fileno(), 0x8915,  # SIOCGIFADDR
                                        struct.pack('256s', ifname[:15]))[20:24])


def transfer_time_reformat(goal_time):
    '''
    将格式化时间转化为时间戳返回
    '''
    return time.mktime(time.strptime(goal_time, '%Y-%m-%d_%H-%M-%S'))


def hash_md5(date):
    '''
    对给定数据以2048字符截断后分组进行MD5哈希，返回十六进制哈希值
    例如：1d6fee8f94b9e8edb5d7cb2aa8149aa0
    '''
    md5 = hashlib.md5()
    while True:
        temp = date[:2048]
        if temp == '':
            break
        else:
            md5.update(temp)
            date = date[2048:]
    return md5.hexdigest()


def dns_check(url):
    '''
    探测URL的IP
    '''
    if url.find("//") != -1:
        url = url[url.find("//") + 2:]
    if url[-1] == '/':
        url = url[:-1]
    try:
        ip = gethostbyname(url)
    except:
        ip = ''
    return ip


def get_ip_location(url):
    '''
    查找指定URL的IP
    '''
    ip_location = {}
    ip_location['ip'] = dns_check(url)
    ip2loc_result = ip2loc.find(url).split('\t')
    if ip2loc_result[0] == 'illegal IP address':
        ip_location['country'] = ''
        ip_location['city'] = ''
    else:
        ip_location['country'] = ip2loc_result[0]
        if len(ip2loc_result) == 2 and ip2loc_result[0] != ip2loc_result[1]:
            ip_location['city'] = ip2loc_result[1]
        else:
            ip_location['city'] = ''
    return ip_location


def read_config_logging(config_catalog=''):
    '''
    读取logging模块配置文件
    config_catalog: 配置文件路径
    '''
    logger = {}
    LOG_PATH = sys.path[0] + '/log/'
    if config_catalog == '':  # 当为空时去上级目录的config目录下寻找logging_config.yaml配置文件
        parent_path = os.path.realpath('..')
        grandparent_path = os.path.dirname(parent_path)
        config_catalog = pjoin(grandparent_path, 'config')
    config_path = pjoin(config_catalog, "logging_config.yaml")
    if os.path.exists(config_path):
        with open(config_path) as f:
            dictcfg = yaml.load(f)
        dictcfg['handlers']['file_info']['filename'] = pjoin(
            LOG_PATH, dictcfg['handlers']['file_info']['filename'])
        dictcfg['handlers']['file_debug']['filename'] = pjoin(
            LOG_PATH, dictcfg['handlers']['file_debug']['filename'])
        dictcfg['handlers']['file_error']['filename'] = pjoin(
            LOG_PATH, dictcfg['handlers']['file_error']['filename'])
        logging.config.dictConfig(dictcfg)
        logger['logger_console_stdout'] = logging.getLogger("console_stdout")
        logger['logger_console_stderr'] = logging.getLogger("console_stderr")
        logger['logger_file_info'] = logging.getLogger("file_info")
        logger['logger_file_debug'] = logging.getLogger("file_debug")
        logger['logger_file_error'] = logging.getLogger("file_error")
        return logger
    else:
        raise Exception("logging_config file not exist")
        sys.exit(1)


def url_format(url):
    '''
    规范url格式，若url开头无'http://'或'https://'，则加上'http://'
    去掉尾部'/'
    '''
    find_result = url.find("http://")
    if find_result != -1:
        url = url[:find_result] + url[find_result + 7:]
    find_result = url.find("https://")
    if find_result != -1:
        url = url[:find_result] + url[find_result + 8:]
    url = "http://" + url
    if url.endswith('/'):
        url = url[:-1]
    return url


def divide_splist(l, s):
    '''
    将列表l平均分割为n个列表，每个列表s个元素
    '''
    return [l[i:i + int(s)] for i in range(len(l)) if i % int(s) == 0]

if __name__ == '__main__':
    # print get_ip_location('3311986.com')
    print hash_md5('http://10086jger.com')
    pass
