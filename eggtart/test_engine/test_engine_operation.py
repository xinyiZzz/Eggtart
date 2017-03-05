#!/usr/bin/python
#-*-coding:utf-8-*-

'''
Name: 引擎自定义功能
Author：XinYi 609610350@qq.com
Time：2016.5
'''

import sys
import time
import copy
import threading
import json
from os.path import join as pjoin
sys.path.append('../server_base')
from threadpool_spark import ThreadPoolSpark
from utils import read_config_logging
logger = read_config_logging()

class TestEngineOperation():

    '''
    定义任务具体执行操作
    '''

    def __init__(self, pool_num=10):
        self.pool = ThreadPoolSpark(pool_num)  # 创建线程池
        self.task_result_list = []  # 任务结果列表

    def update_task_list(self, one_task_result):
        '''
        多线程操作共享的类对象资源，互斥访问,
        将每个线程处理的结果存入self.task_result_list
        '''
        if self.task_lock.acquire():
            self.task_result_list.append(one_task_result)
            self.task_lock.release()

    @staticmethod
    def defined_operate(self, one_task):
        '''
        引擎的对任务处理的核心操作，此处one_task为task_list中的一个任务，
        将{时间戳: one_task['url']}写入one_task['path']指定目录下，
        并在将结果拼接到任务后面写入结果队列
        '''
        url = one_task['url']
        logger['logger_file_debug'].debug(url)
        if 'path' in one_task:
            path = one_task['path']
            with open(pjoin(path, str(time.time())), 'w') as f:
                task_result = {url: path}
                json.dump(task_result, f)
        task = copy.copy(one_task)  # 设计python深复制浅复制的问题
        task['result'] = 'TestEngine run win! ' + url 
        self.update_task_list(task)

    def task_operate(self, task_list):
        '''
        TestEngine调用接口，接受任务并处理
        '''
        self.task_lock = threading.Lock()  # 线程锁
        self.task_result_list = []  # 每个任务执行前初始化结果列表
        # 将任务列表及对应处理函数传入线程池，
        # 线程池会将task_list中每个任务分别在多个线程中调用defined_operate函数处理
        for task in task_list:
            self.pool.run(func=self.defined_operate,
                          args=(self, task))
        self.pool.wait()


if __name__ == '__main__':
    test = TestEngineOperation(pool_num=10)
    task_list = [{'url': 'test_web1', 'path': './test_data/web1'}]
    test.task_operate(task_list)
