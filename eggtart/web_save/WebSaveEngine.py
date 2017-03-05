#!/usr/bin/env python
# coding: utf-8

'''
Name: 网页保存引擎
Author：YunLong/XinYi 609610350@qq.com
Time：2016.4
'''

import sys
import time
sys.path.append('../server_base')
from web_save_start import WebSavestart
from Engine_Model import Engine_Model


class WebSaveEngine(Engine_Model):

    # def __init__(self, config_name='web_save_html_conf.yaml'): # 以仅保存网页html的模式启动
    def __init__(self, config_name='web_save_conf.yaml'): # 以保存网页完整信息的模式启动
        super(WebSaveEngine, self).__init__(config_name)
        pass

    def read_config(self):
        self.pool_num = self.user_config.web_save.pool_num

    def init_object(self):
        '''
        初始化类操作对象
        '''
        self.web_save = WebSavestart(self.pool_num)

    def handle_task(self, task_list):
        '''
        任务处理函数，执行具体调用
        '''
        self.web_save.task_operate(task_list)
        return self.web_save.task_result_list


if __name__ == '__main__':
    WebSave = WebSaveEngine()
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            WebSave.start()
        elif 'stop' == sys.argv[1]:
            WebSave.stop()
        elif 'restart' == sys.argv[1]:
            WebSave.restart()
        else:
            print 'unknown command'
            sys.exit(2)
        sys.exit(0)
    else:
        print 'usage: %s start|stop|restart' % sys.argv[0]
        sys.exit(2)
