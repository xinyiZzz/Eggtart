#!/usr/bin/env python
# coding: utf-8
'''
Name: 守护进程管理基类测试
Author：XinYi 609610350@qq.com
2015.10.3
'''

import sys
import time

from daemonize import _Daemonize


class TestEngine(_Daemonize):

    def __init__(self):
        super(TestEngine, self).__init__()

    def start_operation(self):
        while 1:
            time.sleep(5)
            print 'live'
    
    def stop_operation(self):
        print 'Daemonize over'

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
