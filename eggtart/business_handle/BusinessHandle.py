#!/usr/bin/env python
# coding: utf-8

'''
Name: 业务调度引擎
Author：
Time：2016.7
'''

import os
import sys
import time
import traceback
import copy
sys.path.append('../server_base')
from mysql_scheduler import MysqlScheduler
from Engine_Model import Engine_Model, task_error_extract_deco, child_process_manage_deco


class BusinessHandle(Engine_Model):

    def __init__(self, config_name='business_handle_conf.yaml'):
        super(BusinessHandle, self).__init__(config_name)
        pass

    def read_config(self):
        '''
        读取额外的配置文件部分，
        框架会读取所有引擎共有的server、beanstalkc、mysql的配置文件部分
        '''
        pass

    def init_object(self):
        '''
        初始化引擎具体操作类，在引擎python TestEngine.py start时仅调用一次
        '''
        self.mysql_scheduler = MysqlScheduler(self.mysql_host,
                                              self.mysql_db, self.mysql_user, self.mysql_password)

    @child_process_manage_deco()
    @task_error_extract_deco()
    def task_extract(self, job_body):
        '''
        任务处理函数，执行具体调用。框架内部循环监听引擎任务启动队列
        (/config/XXX_conf.yaml的queue_start_name字段指定)
        对接收到的每个任务调用这个函数执行
        '''
        job_body = copy.copy(job_body)
        return self.mysql_scheduler.task_operate(job_body)

if __name__ == '__main__':
    engine = BusinessHandle()
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            engine.start()
        elif 'stop' == sys.argv[1]:
            engine.stop()
        elif 'restart' == sys.argv[1]:
            engine.restart()
        else:
            print 'unknown command'
            sys.exit(2)
        sys.exit(0)
    else:
        print 'usage: %s start|stop|restart' % sys.argv[0]
        sys.exit(2)
