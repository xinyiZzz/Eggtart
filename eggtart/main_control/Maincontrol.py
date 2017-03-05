#!/usr/bin/env python
# coding: utf-8

'''
Name: 主控引擎——任务调度
Author：XinYi 609610350@qq.com
Time：2016.5.26
'''

import sys
import os
import copy
import time
import threading
import multiprocessing
import atexit
import traceback
sys.path.append('.')
sys.path.append('../server_base')

from Engine_Model import Engine_Model, child_process_manage_deco, task_error_extract_deco
from mysql_handle_base import MysqlHandleBase
from beanstalk_handle import BeanstalkHandle
from daemonize import _Daemonize
from utils import hash_md5, get_format_time, transfer_time_reformat, read_config_logging
logger = read_config_logging()

_CURRENT_PATH = sys.path[0]


class MainControl(Engine_Model):

    def __init__(self, config_name='control_conf.yaml'):
        super(MainControl, self).__init__(config_name)
        self.mysql_handle_base = MysqlHandleBase(mysql_host=self.mysql_host,
                                                 mysql_user=self.mysql_user,
                                                 mysql_password=self.mysql_password,
                                                 mysql_db=self.mysql_db)
        self.engine_describe = self.get_engine_describe()

    def get_engine_describe(self):
        '''
        读取mysql的engine_describe表中对系统中所有引擎描述信息
        '''
        fields = ['engine_type', 'engine_code_name']
        get_result = self.mysql_handle_base.select(
            'engine_describe', fields, fetch_type='all')
        engine_describe = {}
        for engine_info in get_result:
            engine_describe[engine_info['engine_type']
                            ] = engine_info['engine_code_name']
        return engine_describe

    def get_engine_queue(self, engine_type):
        '''
        读取mysql的server_live表获取指定类型引擎信息
        '''
        fields = ['queue_ip', 'queue_start_name', 'queue_result_name']
        where_fields = {'engine_type': [engine_type, 's'],
                        'status': [1, 'd']}
        return self.mysql_handle_base.select(
            'server_live', fields, where_fields, fetch_type='all')

    def read_config(self):
        pass

    def init_object(self):
        '''
        初始化handle_task中使用的操作类对象
        '''
        self.start_engines_among_task_shift()  # 启动引擎结果队列监听线程

    def waiting_engine_get(self, job_body, scheduler):
        '''
        从job_body task_engine串中取出第一个引擎编号放到waiting_engine中
        '''
        run_engine_type = job_body['task_engine'].split('-')[0]
        if hasattr(scheduler, self.engine_describe[run_engine_type]):
            job_body = getattr(scheduler, self.engine_describe[
                               run_engine_type])(job_body)
            job_body['waiting_engine'].append(run_engine_type)
        else:
            job_body['run_error_engine'].append(run_engine_type)
            job_body['error'].append('no task bulid ' + run_engine_type)
        job_body[
            'task_engine'] = '-'.join(job_body['task_engine'].split('-')[1:])
        return job_body

    def waiting_engine_start(self, job_body):
        '''
        发送任务给job_body waiting_engine中的待启动引擎
        '''
        for waiting_engine in job_body['waiting_engine']:  # 并行发送至下一步可同时处理的引擎
            select_result = self.get_engine_queue(waiting_engine)
            if select_result is not False:
                # 获取查询到的第一条记录的queue_start_name，并将任务写入队列
                beanstalk_handle = BeanstalkHandle(
                    host=select_result[0]['queue_ip'])
                beanstalk_handle.put(
                    select_result[0]['queue_start_name'], job_body)
                logger['logger_file_info'].info('put job %s to queue %s' % (
                    job_body['task_id'], select_result[0]['queue_start_name']))
            else:
                job_body['error'].append(
                    'no runnable engine ' + waiting_engine)
                job_body['run_error_engine'].append(waiting_engine)
                job_body['waiting_engine'].remove(waiting_engine)
        return job_body

    def task_pipeline(self, scheduler, job_body):
        '''
        实现任务的流水线串行执行，按照任务信息中task_engine定义的引擎顺序执行任务
        根据任务类型对应的控制器scheduler对需调度的下一引擎输入任务进行构造
        注：只有当该任务当前没有引擎执行时，即running_engine为空时才进行调度
        '''
        # 说明该任务当前有引擎在运行，是其它处理引擎开始任务时发送
        if job_body['running_engine'] != []:
            return job_body
        # 循环调度中，当waiting_engine等于[]时说明调度失败
        while job_body['waiting_engine'] == [] and job_body['task_engine'] != '':
            job_body = self.waiting_engine_get(job_body, scheduler)
            job_body = self.waiting_engine_start(job_body)
        # 待调用引擎抽取
        if job_body['waiting_engine'] == [] and job_body['task_engine'] == '' and job_body['running_engine'] == []:  # 说明该任务结束，所有引擎执行完毕
            job_body['stop_time'] = get_format_time()
            job_body['run_time'] = int(
                time.time() - transfer_time_reformat(job_body['start_time']))
            return job_body
        return job_body

    @task_error_extract_deco()
    def handle_task(self, job_body):
        '''
        任务处理, 根据任务类型选择控制器，构造任务执行流水线中下一引擎的任务信息
        发送任务到该引擎队列
        '''
        if job_body['cmd'] == 'SINGLE_ENGINE_TEST':  # 当接受到单独测试任务时跳过
            return False
        job_body = copy.copy(job_body)
        origin_job_body = copy.copy(job_body)
        self.write_result(job_body)  # 先把调度前的任务作为结果输出
        if 'start_time' not in job_body:
            job_body['start_time'] = get_format_time()
        # 动态加载/scheduler目录下的控制器模块，每个控制器对应一种任务类型cmd
        try:
            moduleList = __import__(
                'scheduler.' + job_body['cmd'], {}, {}, [job_body['cmd']])
            scheduler = getattr(moduleList, job_body['cmd'])(_CURRENT_PATH)
            job_body = self.task_pipeline(scheduler, job_body)
            # 当任务修改，说明发生任务调度，则在task_extract_deco中会输出调度后的结果，反之不输出结果
            if origin_job_body == job_body:
                return False  # 不输出结果
        except ImportError, e:
            job_body['error'].append('no scheduler ' + job_body['cmd'])
            logger['logger_file_info'].info('no scheduler %s, error: %s' %
                                            (job_body['cmd'], e))
        return job_body

    @child_process_manage_deco()
    def task_extract(self, job_body):
        '''
        任务处理
        '''
        return self.handle_task(job_body)

    def get_all_engine_info(self):
        '''
        读取server_live表中除主控、业务处理引擎、测试引擎外的所有引擎的信息，可新增过滤引擎编号
        '''
        sql = "select queue_ip, queue_result_name from server_live where status=1 and engine_type Not REGEXP '00|01|99'"
        return self.mysql_handle_base.select(sql=sql, fetch_type='all')

    def engines_among_task_shift(self):
        '''
        根据server_live表中记录的信息，对当前集群中每一个处理引擎新建一个进程
        监听其任务结果队列，并对队列中的任务取出处理后交给下一个引擎
        '''
        listening_engines = []
        process_records = {}
        while True:
            select_result = self.get_all_engine_info()
            if select_result is not False:
                select_result = reduce(
                    lambda x, y: x if y in x else x + [y], [[], ] + list(select_result))  # 对结果去重
                new_engine = [
                    i for i in select_result if i not in listening_engines]  # 求差集
                stop_engine = [
                    i for i in listening_engines if i not in select_result]
            else:  # 说明已经没有正在运行的引擎，则停止所有监听进程
                new_engine = []
                stop_engine = listening_engines
            for engine_info in new_engine:  # 对新增的引擎，开启进程监听其结果队列
                process_over_sign = multiprocessing.Queue()  # 用于给子进程传送结束标志，初始为空，非空则子进程开始结束
                oneprocess = EnginesAmongTaskShift(
                    self, engine_info, process_over_sign)
                logger['logger_file_info'].info(
                    'listening engine queue %s', str(engine_info))
                oneprocess.start()
                listening_engines.append(engine_info)
                process_records[hash_md5(str(engine_info))] = process_over_sign
            for engine_info in stop_engine:  # 对停止的引擎，向其结束标志队列中添加信息，告诉其自杀
                process_records[hash_md5(str(engine_info))].put("1")
                del(process_records[hash_md5(str(engine_info))])
                listening_engines.remove(engine_info)
                logger['logger_file_info'].info(
                    'stop listening engine queue %s', str(engine_info))
            time.sleep(5)

    def start_engines_among_task_shift(self):
        '''
        开启子线程，进行引擎间任务转移，按照任务信息中task_engine定义的引擎顺序执行
        '''
        t1 = threading.Thread(target=self.engines_among_task_shift)
        t1.setDaemon(True)  # 保证主线程退出时，子线程退出
        t1.start()


class EnginesAmongTaskShift(multiprocessing.Process):

    '''
    循环监听engine_info引擎信息中指定的queue_result_name引擎结果队列，并将其中
    结果调用main_control类的handle_task函数进行处理，将任务传入下一引擎
    '''

    def __init__(self, main_control, engine_info, process_over_sign):
        super(EnginesAmongTaskShift, self).__init__()
        self.main_control = main_control
        self.engine_info = engine_info
        self.process_over_sign = process_over_sign

    def listening_engine_result(self):
        '''
        监听engine_info中指定引擎的结果队列，并调用main_control的task_extract进行处理
        '''
        beanstalk_handle = BeanstalkHandle(host=self.engine_info['queue_ip'])
        for job_msg, job_body in beanstalk_handle.get(self.engine_info['queue_result_name'], infinite_loop=True):
            logger['logger_file_debug'].debug('listening engine %s job %s' %
                                              (str(self.engine_info), job_body))
            self.main_control.handle_task(job_body)

    def start_listening(self):
        '''
        开启子线程，监听engine_info中指定引擎的结果队列
        '''
        t1 = threading.Thread(target=self.listening_engine_result)
        t1.setDaemon(True)  # 保证主线程退出时，子线程退出
        t1.start()

    def run(self):
        self.start_listening()
        _Daemonize.write_process_pid(self.engine_info)  # 在/log目录登记子进程信息
        while self.process_over_sign.empty():  # 接收主进程发送的自杀信息，表明该子进程监听的结果队列对应引擎已停止
            time.sleep(1)
        try:
            sys.exit(1)
        except SystemExit:
            _Daemonize.remove_process_pid()  # 删除登记信息
            logger['logger_file_info'].info(
                'kill listening process %s', os.getpid())


if __name__ == '__main__':
    main_control = MainControl()
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            main_control.start()
        elif 'stop' == sys.argv[1]:
            main_control.stop()
        elif 'restart' == sys.argv[1]:
            main_control.restart()
        else:
            print 'unknown command'
            sys.exit(2)
        sys.exit(0)
    else:
        print 'usage: %s start|stop|restart' % sys.argv[0]
        sys.exit(2)
