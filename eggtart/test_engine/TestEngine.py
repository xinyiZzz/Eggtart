#!/usr/bin/env python
# coding: utf-8

'''
Name: 测试引擎——模版Demo
Author：XinYi 609610350@qq.com
Time：2016.5
'''

import sys
import time
sys.path.append('../server_base')
from test_engine_operation import TestEngineOperation
from Engine_Model import Engine_Model


class TestEngine(Engine_Model):

    def __init__(self, config_name='test_engine_conf.yaml'):
        super(TestEngine, self).__init__(config_name)
        pass

    def read_config(self):
        '''
        读取额外的配置文件部分，
        框架会读取所有引擎共有的server、beanstalkc、mysql的配置文件部分
        '''
        self.pool_num = self.user_config.text.pool_num

    def init_object(self):
        '''
        初始化引擎具体操作类，在引擎python TestEngine.py start时仅调用一次
        '''
        self.test_engine_operation = TestEngineOperation(self.pool_num)

    def handle_task(self, task_list):
        '''
        任务处理函数，执行具体调用。框架内部循环监听引擎任务启动队列
        (/config/test_engine_conf.yaml的queue_start_name字段指定)
        对接收到的每个任务调用这个函数执行
        '''
        self.test_engine_operation.task_operate(task_list)
        return self.test_engine_operation.task_result_list


if __name__ == '__main__':
    test_engine = TestEngine()
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            test_engine.start()
        elif 'stop' == sys.argv[1]:
            test_engine.stop()
        elif 'restart' == sys.argv[1]:
            test_engine.restart()
        else:
            print 'unknown command'
            sys.exit(2)
        sys.exit(0)
    else:
        print 'usage: %s start|stop|restart' % sys.argv[0]
        sys.exit(2)
