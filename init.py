#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Name: 系统初始化，删除所有引擎的日志文件和备份的运行结果
Author：XinYi 609610350@qq.com
Time：2016.5
'''

import os
import sys
from os.path import join as pjoin
import shutil


def init_log():
    '''
    删除所有引擎的日志文件
    '''
    for engine_dir in os.listdir('eggtart'):
        if os.path.isdir('eggtart/' + engine_dir):
            log_path = pjoin('eggtart', engine_dir, 'log')
            if os.path.exists(log_path):
                if os.path.exists(pjoin(log_path, 'engine_stderr.log')):
                    os.remove(pjoin(log_path, 'engine_stderr.log'))
                if os.path.exists(pjoin(log_path, 'engine_stdout.log')):
                    os.remove(pjoin(log_path, 'engine_stdout.log'))

def init_local_result():
    '''
    删除所有引擎备份的运行结果
    '''
    for engine_dir in os.listdir('eggtart'):
        if os.path.isdir('eggtart/' + engine_dir):
            local_result_path = pjoin('eggtart', engine_dir, 'local_result')
            if os.path.exists(local_result_path):
                shutil.rmtree(local_result_path)


if __name__ == '__main__':
    init_log()
    init_local_result()

