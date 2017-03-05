#!/usr/bin/env python
# coding: utf-8
'''
Name: 心跳服务类
Author：XinYi 609610350@qq.com
Time：2015.9.3

输入：
    mysql_config：              mysql数据库连接参数
功能：
    在mysql对应表中记录进程存活状态，自动更新时间字段，其他字段需手动修改后更新
接口：
    register_sever()            心跳注册，添加存活状态
    update_sever()              开启心跳线程，定期更新存活状态
    logout_sever()              心跳退出，删除存活状态
'''
import sys
import time
import threading

from mysql_handle_base import MysqlHandleBase
from utils import get_format_time, getLocalIp


class _ServerHeartBeat(object):

    def __init__(self, mysql_config, table_name, engine_id, engine_type, queue_ip, queue_start_name, queue_result_name, update_interval=60):
        self.mysql_handle = MysqlHandleBase(mysql_config['host'], mysql_config['user'],
                                            mysql_config['password'], mysql_config['db'])
        self.table_name = table_name
        self.engine_type = engine_type
        self.update_interval = update_interval
        self.where_fields = {'engine_id': [engine_id, 's']}
        self.register_fields = {'engine_id': [engine_id, 's'],
                                'ip': [getLocalIp(), 's'],
                                'engine_type': [engine_type, 's'],
                                'queue_ip': [queue_ip, 's'],
                                'queue_start_name': [queue_start_name, 's'],
                                'queue_result_name': [queue_result_name, 's'],
                                'status': [1, 's'],
                                'time': [get_format_time(), 's']}
        self.update_fields = {}

    def reset_update_fields(self, update_fields):
        '''
        设置服务端更新变量
        '''
        for field in update_fields:
            self.update_fields[field] = update_fields[field]

    def register_sever(self):
        '''
        守护进程(服务)在数据库server_live表中注册信息
        '''
        select_result = self.mysql_handle.select(
            self.table_name, ['*'], self.where_fields, fetch_type='one')
        if select_result is not False:
            self.mysql_handle.delete(self.table_name, self.where_fields)
        insert_result = self.mysql_handle.insert(
            self.table_name, self.register_fields)
        sys.stdout.write('%s: server register win\n' % (time.ctime(),))

    def once_update_sever(self):
        '''
        执行线程工作，定时更新数据库，记录服务存活
        '''
        while True:
            self.update_fields = {}
            time.sleep(self.update_interval)
            self.reset_update_fields({'time': [get_format_time(), 's']})
            self.mysql_handle.update(
                self.table_name, self.update_fields, self.where_fields)

    def update_sever(self):
        '''
        开启子线程，定期检查服务是否存活
        '''
        t1 = threading.Thread(target=self.once_update_sever)
        t1.setDaemon(True) # 保证主线程退出时，子线程退出
        t1.start()

    def logout_sever(self):
        '''
        守护进程(服务)将之前注册在数据库server_live表中信息删除。
        '''
        self.mysql_handle.delete(self.table_name, self.where_fields)
        sys.stdout.write('%s: server logout win\n' % (time.ctime(),))

if __name__ == '__main__':
    mysql_config = {'db': 'test',
                    'host': '127.0.0.1',
                    'user': 'root',
                    'password': 'zxy'}
    server_heart_beat = _ServerHeartBeat(
        mysql_config, 'server_live', 'test', '00', 1, update_interval=2)
    server_heart_beat.register_sever()
    server_heart_beat.update_sever()
    time.sleep(10)
    server_heart_beat.logout_sever()
