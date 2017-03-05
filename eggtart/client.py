#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Name: 系统框架——客户端  用于向系统中引擎发送运行指令
Author：XinYi 609610350@qq.com
Time：2016.4
'''

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s-[%(asctime)s][%(module)s][%(funcName)s][%(lineno)d]: %(message)s')

import sys
import time
import argparse
import copy
import pprint
import hashlib
import json
import os
from os.path import join as pjoin

sys.path.append(".")
sys.path.append('./eggtart/server_base')
sys.path.append('./server_base')
from errors import NotImplemented
from config_read import Config
from beanstalk_handle import BeanstalkHandle

pp = pprint.PrettyPrinter(indent=4)

# 命令模版定义，用于对应指令的参数是否符合要求
avaliable_cmds = {
    'COMPLETE_TASK_TEST': {},# 完整格式任务运行指令
    'SINGLE_ENGINE_TEST': {  # 单引擎运行指令
        'task_list': {
            'value': [],
            'validation': lambda x: len(x) > 0
        },
        'output': {
            'value': 'all',
            # all表示即输出到结果队列，也输出到本地文件
            'validation': lambda x: x in ['all', 'local', 'queue']
        },
        'error': {  # 运行过程中产生的错误
            'value': []
        }
    },
    'ENGINE_TEST': {  # 测试任务运行指令
        'task_name': {
            'value': 'engine_test',
            'validation': lambda x: len(x) < 50
        },
        'add_way': {
            'value': 'test',
            'validation': lambda x: len(x) > 0
        },
        'task_engine': {
            'value': '02-99',  # 任务调用的引擎列表，按照顺序依次执行02-99
            'validation': lambda x: len(x) > 0
        },
        'url_list': {
            'value': [],
            'validation': lambda x: len(x) > 0
        },
        'output': {
            'value': 'all',
            # all表示即输出到结果队列，也输出到本地文件
            'validation': lambda x: x in ['all', 'local', 'queue']
        },
        'task_list': {  # 引擎间流水线处理的任务列表
            'value': []
        },
        'waiting_engine': {  # 当前待运行引擎，即添加到引擎启动队列，但未执行
            'value': []
        },
        'running_engine': {  # 当前任务正在运行的引擎
            'value': []
        },
        'run_win_engine': {  # 运行结束的引擎
            'value': []
        },
        'run_error_engine': {  # 运行结束的引擎
            'value': []
        },
        'run_state': {  # 任务运行状态，及调用了哪个引擎、开始时间、结束时间等
            'value': []  # [{'engine_id': , 'start_time': ,'stop_time':}, ]
        },
        'error': {  # 运行过程中产生的错误
            'value': []
        }
    },
    'ONE_ENGINE_TEST': {},  # 和GRAYS_CHECK相同，将ONE_GRAYS_CHECK转换为GRAYS_CHECK指令再进行处理
    'LIST_SERVERS': {},
    'SERVER_QSIZES': {},
}


def hash_cmd(cmd):
    '''
    对待添加队列的指令进行hash
    '''
    return hashlib.md5(json.dumps(cmd)).hexdigest()


def new_cmd(command, args_dict):
    '''
    根据指令command类型，选择avaliable_cmds中的指令模版，查看args_dict中的参数
    是否符合模版中定义的各参数要求
    '''
    cmd_template = avaliable_cmds[command]
    cmd = {'cmd': command}
    for k in cmd_template:
        cmd[k] = args_dict[k] if ((k in args_dict) and (
            args_dict[k] is not None)) else cmd_template[k]['value']
        if ('validation' in cmd_template[k] and cmd_template[k]['validation']):
            if (not cmd_template[k]['validation'](cmd[k])):
                raise Exception("%s: %s failed validation" % (k, cmd[k]))
    cmd['task_id'] = hash_cmd(cmd) + str(int(time.time() * 10000))
    cmd['create_time'] = time.strftime(
        '%Y-%m-%d_%H-%M-%S', time.localtime(time.time()))
    return cmd

def divide_splist(l, s):
    '''
    将列表l平均分割为n个列表，每个列表s个元素
    '''
    return [l[i:i + int(s)] for i in range(len(l)) if i % int(s) == 0]


def run_cmd(config, args):
    '''
    根据配置文件和指令参数构造指令，并发送到指令服务的队列中
    '''
    if (args.command not in avaliable_cmds):
        raise Exception("not a valid command...")
    beanstalk_handle = BeanstalkHandle(host=config.beanstalkc.queue_ip)
    if (args.command == 'COMPLETE_TASK_TEST'):
        args_dict = copy.copy(args.__dict__)
        if (not os.path.exists(args.task_info_list)):
            raise Exception("task info json doesn't exist... ")
        with open(os.path.abspath(args.task_info_list), 'rb') as f:
            cmd = json.load(f)
        beanstalk_handle.put(config.beanstalkc.queue_start_name, cmd)
    elif (args.command == 'SINGLE_ENGINE_TEST'):
        args_dict = copy.copy(args.__dict__)
        if (not os.path.exists(args.task_info_list)):
            raise Exception("task info json doesn't exist... ")
        with open(os.path.abspath(args.task_info_list), 'rb') as f:
            task_list = json.load(f)
            task_list = [task_list] if not args.group_num else divide_splist(
                task_list, args.group_num)
            for split_task_list in task_list:
                args_dict['task_list'] = split_task_list
                cmd = new_cmd(args.command, args_dict)
                beanstalk_handle.put(config.beanstalkc.queue_start_name, cmd)
    elif (args.command.startswith('ONE_')):  # 处理开头是ONE_且基于url_list为参数的指令
        new_command = args.command[4:]
        args_dict = copy.copy(args.__dict__)
        args_dict['url_list'] = [args.url]
        cmd = new_cmd(new_command, args_dict)
        beanstalk_handle.put(config.beanstalkc.queue_start_name, cmd)
    elif (args.command == 'START_SERVER'):
        raise NotImplemented("NotImplemented yet...")
    elif (args.command == 'STOP_SERVER'):
        raise NotImplemented("NotImplemented yet...")
    elif (args.command == 'LIST_SERVERS'):
        raise NotImplemented("NotImplemented yet...")
    elif (args.command == 'SERVER_QSIZES'):
        raise NotImplemented("NotImplemented yet...")
    else:
        # 处理批量URL检测任务
        args_dict = copy.copy(args.__dict__)
        if (not os.path.exists(args.url_list)):
            raise Exception("url list json doesn't exist... ")
        with open(os.path.abspath(args.url_list), 'rb') as f:
            url_list = json.load(f)
            url_list = [url_list] if not args.group_num else divide_splist(
                url_list, args.group_num)
            for split_task_list in url_list:
                args_dict['url_list'] = split_task_list
                cmd = new_cmd(args.command, args_dict)
                beanstalk_handle.put(config.beanstalkc.queue_start_name, cmd)


def read_config(config_path):
    '''
    读取配置文件
    '''
    if not os.path.isabs(config_path):
        config_path = pjoin('./config', config_path)
    if os.path.exists(config_path):
        config = Config(config_path)  # 导出配置文件到user_config对象
    else:
        logger.error('config file not exist')
        sys.exit(1)
    return config


def print_avaliable_cmd():
    '''
    当客户端出错时，返回所有指令的描述及参数要求
    '''
    dictionary = {
        '-c/--config': "config.yaml that in ./config dir, contains a) server info; b) beanstalkc connection string;",
        '-cmd/--command': "the cmd you want to run, e.g., \"ENGINE_TEST\"",
        '-ti/--task_info_list': "the location of the json file for task list",
        '-urls/--url_list': "the location of the json file for url list",
        '-gn/--group_num': "the num of the group for task info or url list, default None",
        '-url/--url': "a url you want to check",
        '-tn/-task_name': "the task_name",
        '-aw/--add_way': "the add_way",
        '-te/--task_engine': "the task_engine (e.g., '99-01-02' or '07-10'",
        '-o/--output': "the location of the output json file for task result, default None",
        '-qip/--queue_ip': "Task to send beanstalkc server IP", 
        '-qsn/--queue_start_name': "Task to send beanstalkc engine start queue name"
    }
    cmds = {'SINGLE_ENGINE_TEST': {
        '-c/--config': dictionary['-c/--config'],
        '-cmd/--command': dictionary['-cmd/--command'],
        '-ti/--task_info_list': dictionary['-ti/--task_info_list'],
        '-gn/--group_num': dictionary['-gn/--group_num'],
        '-o/--output': dictionary['-o/--output'],
        '-qip/--queue_ip': dictionary['-qip/--queue_ip'],
        '-qsn/--queue_start_name': dictionary['-qsn/--queue_start_name']
    }, 'ENGINE_TEST': {
        '-c/--config': dictionary['-c/--config'],
        '-cmd/--command': dictionary['-cmd/--command'],
        '-urls/--url_list': dictionary['-urls/--url_list'],
        '-tn/-task_name': dictionary['-tn/-task_name'],
        '-aw/--add_way': dictionary['-aw/--add_way'],
        '-te/--task_engine': dictionary['-te/--task_engine'],
        '-gn/--group_num': dictionary['-gn/--group_num'],
        '-o/--output': dictionary['-o/--output'],
        '-qip/--queue_ip': dictionary['-qip/--queue_ip'],
        '-qsn/--queue_start_name': dictionary['-qsn/--queue_start_name']
    }, 'ONE_ENGINE_TEST': {
        '-c/--config': dictionary['-c/--config'],
        '-cmd/--command': dictionary['-cmd/--command'],
        '-url/--url': dictionary['-url/--url'],
        '-tn/-task_name': dictionary['-tn/-task_name'],
        '-aw/--add_way': dictionary['-aw/--add_way'],
        '-te/--task_engine': dictionary['-te/--task_engine'],
        '-gn/--group_num': dictionary['-gn/--group_num'],
        '-o/--output': dictionary['-o/--output'],
        '-qip/--queue_ip': dictionary['-qip/--queue_ip'],
        '-qsn/--queue_start_name': dictionary['-qsn/--queue_start_name']
    },'COMPLETE_TASK_TEST': {
        '-c/--config': dictionary['-c/--config'],
        '-cmd/--command': dictionary['-cmd/--command'],
        '-ti/--task_info_list': dictionary['-ti/--task_info_list'],
        '-qip/--queue_ip': dictionary['-qip/--queue_ip'],
        '-qsn/--queue_start_name': dictionary['-qsn/--queue_start_name']
    }}

    for k, v in cmds.iteritems():
        print('')
        print('\t%s:' % k)
        for kk, vv in v.iteritems():
            print('\t\t%s: %s' % (kk, vv))

    print('')


class VitrualObject():

    '''
    以对象的形式提供变量。例如a.b调用
    '''

    def __init__(self, variate=None, value=None):
        pass

    def set(self, variate, value):
        setattr(self, variate, value)

def VitrualConfig(args):
    '''
    当客户端参数中没有config配置文件，而是直接将配置项以参数形式提供时，将这些
    参数初始化同read_config函数返回结果一样的配置信息调用方式
    '''
    vitrual_config = VitrualObject()
    beanstalkc_object = VitrualObject()
    beanstalkc_object.set('queue_ip', args.queue_ip)
    beanstalkc_object.set('queue_start_name', args.queue_start_name)
    vitrual_config.set('beanstalkc', beanstalkc_object)
    return vitrual_config


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        '-c', '--config', help="config.yaml that in ../config dir, contains a) server info; b) beanstalkc connection string;", required=False)
    parser.add_argument(
        '-cmd', '--command', help="the cmd you want to run, e.g., \"ENGINE_TEST\"", required=True)
    parser.add_argument(
        '-ti', '--task_info_list', help="the location of the json file for task info", required=False)
    parser.add_argument(
        '-urls', '--url_list', help="the location of the json file for url list", required=False)
    parser.add_argument(
        '-gn', '--group_num', help="the num of the group for task info or url list, default None", default=30)
    parser.add_argument(
        '-url', '--url', help="a url you want to check", required=False)
    parser.add_argument(
        '-tn', '--task_name', help="the task_name", required=False)
    parser.add_argument(
        '-aw', '--add_way', help="the add_way", required=False)
    parser.add_argument(
        '-te', '--task_engine', help="the task_engine (e.g., '99-01-02' or '07-10'", required=False)
    parser.add_argument(
        '-o', '--output', help="the location of the output json file for task result, default None", required=False)
    parser.add_argument(
        '-qip', '--queue_ip', help="Task to send beanstalkc server IP", required=False)
    parser.add_argument(
        '-qsn', '--queue_start_name', help="Task to send beanstalkc engine start queue name", required=False)

    try:
        args = parser.parse_args()
        logger.info('client request args: %s', args)
        if args.command == 'HELP':
            print_avaliable_cmd()
            quit()
        if args.config != None: # 当参数中有配置文件时
            config = read_config(args.config)
        else: # 当参数中没有配置文件时，config形式一样
            config = VitrualConfig(args)
        run_cmd(config, args)
    except Exception as exc:
        print_avaliable_cmd()
        logger.error(exc)
        raise        
