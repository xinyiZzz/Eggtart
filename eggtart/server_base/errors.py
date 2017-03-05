#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Name: 异常处理重定义
Author：XinYi 609610350@qq.com
Time: 2015.5
'''

import time


class DependencyNotInstalledError(Exception):  # 依赖的库没有安装

    def __init__(self, dep):
        self.dep = dep

    def __str__(self):
        return 'lacking of dependency: %s' % self.dep


class ConfigurationError(Exception):  # 配置参数（文件）错误

    def __init__(self, dep):
        self.dep = dep

    def __str__(self):
        return 'Error because config cannot open: %s' % self.dep


class MySQLError(Exception):  # 数据库存储错误

    def __init__(self, dep):
        self.dep = dep

    def __str__(self):
        try:
            return "%s  Mysql Error %d: %s" % \
                (time.ctime(), self.dep.args[0], self.dep.args[1])
        except IndexError:
            return "%s  Mysql Error %s" % (time.ctime(), self.dep.args)


class MongoError(Exception):  # 数据库存储错误

    def __init__(self, dep):
        self.dep = dep

    def __str__(self):
        try:
            return "%s  Mongo Error %d: %s" % \
                (time.ctime(), self.dep.args[0], self.dep.args[1])
        except IndexError:
            return "%s  Mongo Error %s" % (time.ctime(), self.dep.args)


class SocketError(Exception):  # socket错误

    def __init__(self, dep, state):
        self.dep = dep
        self.state = state

    def __str__(self):
        return "%s  Socket Error %d: %s in %s" % (time.ctime(),
                                                  self.dep.args[0], self.dep.args[1], self.state)


class OtherError(Exception):  # 操作错误

    def __init__(self, dep, state):
        self.dep = dep
        self.state = state

    def __str__(self):
        return "%s  Error: %s in %s" % (time.ctime(), self.dep, self.state)

class NotImplemented(Exception):
    pass
