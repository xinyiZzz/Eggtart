#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Name: 主控引擎——测试任务调度
Author：XinYi 609610350@qq.com
Time：2016.5.26
'''

import sys
import os
from os.path import join as pjoin
sys.path.append('../server_base')
from utils import read_config_logging
logger = read_config_logging()


class ENGINE_TEST(object):

    '''
    可疑网站检测任务调度模块，流水线任务引擎调度时，对下一个即将调用的引擎构造
    其所需的输入任务格式，每个函数对应下一个即将调用引擎的名称, 函数参数仅有job_body
    _CURRENT_PATH：*/main_control目录，在动态加载控制器时，由于在守护进程中运行，
    控制器先定位目录再加载其它模块
    '''

    def __init__(self, _CURRENT_PATH):
        '''
        由于在守护进程中启动，所以根据传入的*/main_control路径，
        动态加载/server_base里面的模块
        '''
        sys.path.append(pjoin(pjoin('/'.join(_CURRENT_PATH.split('/')[:-1]), 'server_base'))) # 添加/server_base目录到sys.path
        moduleList = __import__('hash_path_builder', {}, {}, ['get_web_hash_path_abs']) # 加载*/server_base/hash_path_builder.get_web_hash_path_abs
        self.get_web_hash_path_abs = getattr(moduleList, 'get_web_hash_path_abs') # 获取get_web_hash_path_abs方法
        self.WEB_INFO_ROOT_PATH = pjoin('/'.join(_CURRENT_PATH.split('/')[:-2]), 'web_info')

    def web_save(self, job_body):
        '''
        网页信息保存引擎输入任务构造
        '''
        run_engine_type = job_body['task_engine'].split('-')[0]
        if run_engine_type == '02':  # 网页下载引擎(下载完整网页)
            save_type = 'all'
            save_path = 'complete_save_web'
        elif run_engine_type == '03':  # 网页下载引擎(仅下载HTML)
            save_type = 'html'
            save_path = 'signal_save_web'
        if job_body['task_list'] == []:
            url_list = job_body['url_list']
            for url in url_list:
                job_body['task_list'].append({'url': url, 'save_type': save_type, 'save_path': self.get_web_hash_path_abs(url, pjoin(self.WEB_INFO_ROOT_PATH, save_path), 1)})
        else:
            new_task_list = []
            for task in job_body['task_list']:
                task['save_type'] = save_type
                new_task_list.append(task)
            job_body['task_list'] = new_task_list
        return job_body

    def test_engine(self, job_body):
        '''
        测试引擎输入任务构造
        '''
        return job_body
