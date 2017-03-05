#!/usr/bin/python
#-*-coding:utf-8-*-
'''
Name: 系统框架——eggtart引擎基类
Author：XinYi/Bboy 609610350@qq.com
Time：2016.5.15
'''

import os
import sys
import traceback
import json
import beanstalkc
import copy
import time
import multiprocessing

from daemonize import _Daemonize, LOG_PATH
from server_heart_beat import _ServerHeartBeat
from config_read import Config
from os.path import join as pjoin
from beanstalk_handle import BeanstalkHandle
from utils import hash_md5, get_format_time, getLocalIp, read_config_logging

DEFAULT_MAX_TASK_PROCESS_NUM = 10  # 默认最多可同时响应的任务数量，每个任务对应一个子进程


def child_process_manage_deco():
    '''
    任务处理方法装饰器，封装子进程管理、错误处理等功能
    '''
    def _deco(func):
        def __deco(self, job_body, mq, lock):
            _Daemonize.write_process_pid(job_body)
            lock.acquire()
            mq.put(1)
            lock.release()
            func(self, job_body)
            if not mq.empty():
                mq.get(False)
            _Daemonize.kill_child_process()
        return __deco
    return _deco


def task_error_extract_deco(error_func_type=False):
    '''
    任务处理方法装饰器，封装子进程管理、错误处理等功能
    '''
    def _deco(func):
        def __deco(self, job_body):
            try:
                job_body = func(self, job_body)
            except Exception, e:
                self.logger['logger_file_error'].error('task_extract error %s', e)
                self.logger['logger_file_error'].error(traceback.format_exc())
                job_body['error'].append('task_extract engine_type: %s, engine_id: %s, task_id: %s, error: %s' % (
                    self.engine_type, self.engine_id, job_body['task_id'], e))
                if error_func_type != False:
                    job_body = self.error_func(job_body)
            self.write_result(job_body)  # 表明任务结束
        return __deco
    return _deco


class Engine_Model(_Daemonize):

    '''
    引擎框架, 封装通用配置文件读取、引擎心跳检测、beanstalk队列中任务获取、
    任务结果回写等操作
    '''

    def __init__(self, config_name='test_engine_conf.yaml'):
        super(Engine_Model, self).__init__()
        self.config_name = config_name
        self.CURRENT_PATH = sys.path[0]
        self.read_config_public()
        self.engine_id = hash_md5(
            getLocalIp() + self.engine_type + self.CURRENT_PATH)
        self.mq = multiprocessing.Queue()
        self.lock = multiprocessing.Lock()
        self.start_server_heart_beat()

    def read_config_public(self):
        '''
        读取引擎配置文件
        '''
        parent_path = os.path.realpath('..')
        grandparent_path = os.path.dirname(parent_path)
        config_catalog = pjoin(grandparent_path, 'config')
        self.logger = read_config_logging(config_catalog)  # 读取logging模块配置文件
        config_path = pjoin(config_catalog, self.config_name)
        if os.path.exists(config_path):
            self.user_config = Config(config_path)  # 导出配置文件到user_config对象
        else:
            self.logger['logger_file_error'].error('engine config file not exist')
            sys.exit(1)
        self.engine_type = self.user_config.engine.type
        self.queue_ip = self.user_config.beanstalkc.queue_ip
        self.queue_start_name = self.user_config.beanstalkc.queue_start_name
        self.queue_result_name = self.user_config.beanstalkc.queue_result_name
        self.mysql_host = self.user_config.mysql.mysql_host
        self.mysql_db = self.user_config.mysql.mysql_db
        self.mysql_user = self.user_config.mysql.mysql_user
        self.mysql_password = ''
        if self.user_config.mysql.mysql_password is not None:
            self.mysql_password = self.user_config.mysql.mysql_password
        if hasattr(self.user_config.engine, 'max_task_process_num'):
            self.max_task_process_num = self.user_config.engine.max_task_process_num
        else:
            self.max_task_process_num = DEFAULT_MAX_TASK_PROCESS_NUM
            self.logger['logger_file_info'].info(
                'default max_task_process_num: %s', self.max_task_process_num)
        self.read_config()

    def read_config(self):
        '''
        每个引擎读取每类引擎特有的配置文件参数
        '''
        pass

    def start_server_heart_beat(self):
        '''
        创建心跳检测对象，可以定时更新数据库，并记录存活状态
        '''
        mysql_config = {'db': self.mysql_db,
                        'host': self.mysql_host,
                        'user': self.mysql_user,
                        'password': self.mysql_password}
        self.server_heart_beat = _ServerHeartBeat(
            mysql_config, 'server_live', self.engine_id, self.engine_type, self.queue_ip, self.queue_start_name, self.queue_result_name, update_interval=60)

    def write_to_beanstalkc(self, job_body):
        '''
        将任务job_body写回结果队列 queue_result_name
        '''
        self.beanstalk_handle.put(self.queue_result_name, job_body)

    def write_result_to_local_result(self, job_body):
        '''
        每一个任务执行完成后调用，将任务执行结果保存到本地
        '''
        output_path = pjoin(self.CURRENT_PATH, 'local_result')
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        file_name = str(int('%u' % (time.time() * 10000))) + '.json'
        with open(pjoin(output_path, file_name), 'w') as f:
            f.write(json.dumps(job_body))

    def write_result(self, job_body):
        '''
        输出任务结果
        '''
        try:
            if job_body is False or 'output' not in job_body:
                return False
        except:
            self.logger['logger_file_info'].info('error %s',
                                  job_body)
            raise
        if job_body['output'] == 'queue' or job_body['output'] == 'all':
            self.write_to_beanstalkc(job_body)
            self.logger['logger_file_info'].info(
                'queue output result job task_id %s', job_body['task_id'])
        if job_body['output'] == 'local' or job_body['output'] == 'all':
            self.write_result_to_local_result(job_body)
            self.logger['logger_file_info'].info(
                'local output result job task_id %s', job_body['task_id'])
        return True

    def init_object(self):
        '''
        初始化handle_task中使用的操作类对象
        '''
        pass

    def handle_task(self, task_list):
        '''
        任务处理函数，执行具体调用
        输入task_list: queue_start_name队列中获取的一条记录，代表一组任务
        输出task_result_list
        '''
        return task_list

    def error_func(self, job_body):
        '''
        装饰器task_extract_deco中调用，当task_extract中出错时，执行的对应任务的
        信息处理方法
        '''
        job_body = copy.copy(job_body)
        if job_body['cmd'] == 'ENGINE_TEST':
            job_body['run_error_engine'].append(self.engine_type)
            job_body['running_engine'].remove(self.engine_type)
            job_body['run_state'][-1][self.config_name +
                                      '_over_time'] = get_format_time()  # 添加任务完成时间
        return job_body

    @child_process_manage_deco()
    @task_error_extract_deco(error_func_type=True)
    def task_extract(self, job_body):
        '''
        任务处理，包括任务执行状态的记录，并从任务中提取出引擎要处理的数据，
        调用handle_task处理任务，默认为任务中的task_list字段,
        添加新的任务类型时，当需要对除task_list之外的其它任务信息进行处理时，
        需要增加 if job_body['cmd'] == 'XX' 时的处理方法，并在self.error_func中
        增加出错时对应任务的信息处理方法
        '''
        job_body = copy.copy(job_body)
        if 'task_list' not in job_body or job_body['task_list'] == []:
            raise Exception("task_list not found or equal None")
        if job_body['cmd'] == 'ENGINE_TEST':
            job_body['running_engine'].append(self.engine_type)
            run_state = {self.config_name + '_engine_type': self.engine_type,
                         self.config_name + '_engine_id': self.engine_id,
                         self.config_name + '_start_time': get_format_time()}
            # 添加任务开始时间，默认情况下，引擎开始执行任务前，会发送任务开始状态到结果队列
            job_body['run_state'].append(run_state)
            if self.engine_type in job_body['waiting_engine']:
                job_body['waiting_engine'].remove(self.engine_type)
            self.write_result(job_body)  # 写回任务到结果队列，表明任务开始
            job_body['task_list'] = self.handle_task(job_body['task_list'])
            job_body['run_win_engine'].append(self.engine_type)
            job_body['running_engine'].remove(self.engine_type)
            job_body['run_state'][-1][self.config_name +
                                      '_over_time'] = get_format_time()  # 添加任务完成时间
        else:  # 不更新任务状态信息，例如当'cmd'=='SINGLE_ENGINE_TEST'进行单独测试时
            self.write_result(job_body)  # 写回任务到结果队列，表明任务开始
            job_body['task_list'] = self.handle_task(job_body['task_list'])
        return job_body

    def start_operation(self):
        '''
        守护进程启动后入口函数
        '''
        self.logger['logger_file_info'].info('\n****************engine server start*********************\n')
        self.logger['logger_file_debug'].debug('\n****************engine server start*********************\n')
        self.logger['logger_file_error'].error('\n****************engine server start*********************\n')
        self.server_heart_beat.register_sever()
        self.server_heart_beat.update_sever()
        self.beanstalk_handle = BeanstalkHandle(host=self.queue_ip)
        self.init_object()
        for job_msg, job_body in self.beanstalk_handle.get(self.queue_start_name, infinite_loop=True):
            self.logger['logger_file_info'].info('get job task_id %s', job_body['task_id'])
            while self.mq.qsize() >= self.max_task_process_num:
                time.sleep(1)
            proc = multiprocessing.Process(
                target=self.task_extract, args=(job_body, self.mq, self.lock))
            proc.start()

    def stop_operation(self):
        '''
        守护进程结束时运行函数
        '''
        self.logger['logger_file_info'].info('\n^^^^^^^^^^^^^^^^^^^engine server stop^^^^^^^^^^^^^^^^^^^\n')
        self.logger['logger_file_debug'].debug('\n^^^^^^^^^^^^^^^^^^^engine server stop^^^^^^^^^^^^^^^^^^^\n')
        self.logger['logger_file_error'].error('\n^^^^^^^^^^^^^^^^^^^engine server stop^^^^^^^^^^^^^^^^^^^\n')
        self.logger['logger_file_info'].info('engine stop win, type：%s',
                              self.user_config.engine.type)
        self.server_heart_beat.logout_sever()


if __name__ == '__main__':
    Engine = Engine_Model()
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            Engine.start()
        elif 'stop' == sys.argv[1]:
            Engine.stop()
        elif 'restart' == sys.argv[1]:
            Engine.restart()
        else:
            print 'unknown command'
            sys.exit(2)
        sys.exit(0)
    else:
        print 'usage: %s start|stop|restart' % sys.argv[0]
        sys.exit(2)
