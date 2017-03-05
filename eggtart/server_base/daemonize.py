#!/usr/bin/env python
# coding: utf-8
'''
Name: 守护进程管理基类
Author：XinYi 609610350@qq.com
Time：2015.10.3

功能：
    创建守护进程执行指定程序
    在当前目录创建/log目录存储日志
    对守护进程启动的子进程管理，避免出现僵尸进程
接口：
    start_operation():    守护进程启动后运行，需重写为守护进程启动后执行的程序
    stop_operation():     守护进程结束前运行，需重写为守护进程结束前执行的程序
    write_process_pid():  守护进程启动子进程时，在子进程的run()函数开始时调用，
                            将子进程的pid作为文件名创建到/engine_pids目录下，表明子进程开始
    remove_process_pid(): 子进程结束时调用，删除/engine_pids目录下该子进程pid命名的文件，表明子进程结束
    kill_child_process():  杀掉当前进程，若成功则删除该子进程在/engine_pids目录下文件
/log目录说明：
    engine_stdout.log：   进程正常输出的日志文件
    engine_stderr.log：   进程错误输出的日志文件
    engine_pids：         以子进程的pid作为文件名，存储守护进程所启动的每个子进程中对应任务，用于记录子进程存活状态
    
使用方法：
    启动方式：             python XXX.py start
    关闭方式：             python XXX.py stop
    重启方法：             python XXX.py restart
    查看守护进程状态命令： ps -ef | grep base.py |grep -v grep
    也可使用  kill -9 pid 关闭守护进程
'''
import os
import sys
import time
import json
import atexit
import signal

LOG_PATH = sys.path[0] + '/log/'
if not os.path.exists(LOG_PATH):
    os.mkdir(LOG_PATH)


class _Daemonize(object):

    def __init__(self):

        self.pidfile = LOG_PATH + 'engine.pid'  # 进程文件，记录守护进程的进程号，避免重复启动
        self.stdin = '/dev/null'
        self.stdout = LOG_PATH + 'engine_stdout.log'  # 标准输入流
        self.stderr = LOG_PATH + 'engine_stderr.log'  # 标准输出流
        self.child_process_pids = LOG_PATH + 'engine_pids/'  # 保存子进程id号
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)

    def _daemonize(self, stdin, stdout, stderr):
        '''
        将进程脱离终端，形成守护进程
        '''
        try:
            pid = os.fork()  # 第一次fork，生成子进程，脱离父进程
            if pid > 0:         # pid>0 为父进程
                sys.exit(0)  # 父进程退出
        except OSError, e:
            sys.stderr.write('fork #1 failed: %d (%s)\n' %
                             (e.errno, e.strerror))
            sys.exit(1)

        os.chdir("/")  # 修改工作目录
        os.setsid()  # 设置新的会话连接
        os.umask(0)  # 重新设置文件创建权限

        try:
            pid = os.fork()  # 第二次fork，禁止进程打开终端
            if pid > 0:
                sys.exit(0)  # 父进程退出
        except OSError, e:
            sys.stderr.write('fork #2 failed: %d (%s)\n' %
                             (e.errno, e.strerror))
            sys.exit(1)
        # 重定向文件描述符
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(stdin, 'r')
        so = file(stdout, 'a+')
        se = file(stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

    def delpid(self):
        '''
        删除进程文件，标志守护进程退出
        '''
        os.remove(self.pidfile)
        pidfiles_path = self.child_process_pids
        file_list = os.listdir(pidfiles_path)
        for file_name in file_list:
            os.remove(pidfiles_path + file_name)

    def start(self):
        '''
        启动守护进程
        '''
        try:  # 检查pid文件是否存在以探测是否存在进程
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())  # pid 文件中 存放守护进程的进程号
            pf.close()
        except IOError:
            pid = None
        if pid:  # 进程文件存在并获取到 守护进程号，说明守护进程已经启动，不会重复启动，退出
            sys.stderr.write(
                'pidfile already exist. Daemon already running!\n')
            sys.exit(1)

        sys.stdout.write(
            '\n————  正在开启，请看日志文件 %s ————\n' % LOG_PATH)
        # 与控制台脱离, become daemonize
        self._daemonize(self.stdin, self.stdout, self.stderr)
        # 注册退出函数，根据文件pid判断是否存在进程
        atexit.register(self.delpid)
        pid = str(os.getpid())
        file(self.pidfile, 'w+').write('%s\n' % pid)
        if not os.path.exists(self.child_process_pids):
            os.mkdir(self.child_process_pids)
        sys.stdout.write(
            '\n***********************************************************\n')
        sys.stdout.write('%s: engine server start\n' % (time.ctime(),))
        sys.stderr.write(
            '\n***********************************************************\n')
        sys.stderr.write('%s: engine server start\n' % (time.ctime(),))
        # 调用自定义启动函数
        self.start_operation()

    @staticmethod
    def kill_process(pid, pid_file):
        '''
        根据进程号，杀死该进程
        pid_file: 存储pid的文件
        '''
        try:
            while 1:
                os.kill(int(pid), 9)
                message = '%s  pid %s killing!\n'
                sys.stdout.write(message % (time.ctime(), pid))
                time.sleep(0.1)
        except OSError, err:
            err = str(err)
            if err.find('No such process') > 0:
                if os.path.exists(pid_file):
                    os.remove(pid_file)  # kill杀死进程后，删除进程文件
                message = '%s  pid %s kill win!\n'
                sys.stdout.write(message % (time.ctime(), pid))
                return True  # kill win
            else:
                print str(err)
            message = '%s  pid %s kill error!\n'
            sys.stderr.write(message % (time.ctime(), pid))
            return False  # kill error

    def stop(self):
        '''
        关闭守护进程
        '''
        self.stop_operation()
        # 杀死所有子进程, engine_pids目录下以子进程的id作为文件名
        file_list = os.listdir(self.child_process_pids)
        for file_name in file_list:
            child_pid_file = self.child_process_pids + file_name
            self.kill_process(file_name, child_pid_file)
        # 杀死守护进程, 从pid文件中获取pid
        try:
            pf = file(self.pidfile, 'r')
            pid = pf.read().strip()
            pf.close()
        except IOError:
            pid = None
        if not pid:  # 进程号不存在说明进程已经关闭
            message = '%s  pid_file %s not exist!, process not found\n'
            sys.stderr.write(message % (time.ctime(), self.pidfile))
            return False  # pid_file not exist
        self.kill_process(pid, self.pidfile)
        return True
        sys.exit(1)

    def restart(self):
        '''
        重启守护进程
        '''
        self.stop()
        self.start()

    @staticmethod
    def write_process_pid(process_info, pid=''):
        '''
        守护进程启动子进程时，在子进程的run()函数开始时调用，
        将子进程的pid作为文件名创建到/engine_pids目录下，表明子进程开始
        '''
        if pid == '':
            pid = os.getpid()
        pidfile_path = LOG_PATH + 'engine_pids/' + str(pid)
        with open(pidfile_path, 'a+') as f:
            json.dump(process_info, f)

    @staticmethod
    def remove_process_pid(pid=''):
        '''
        子进程结束时调用，删除/engine_pids目录下该子进程pid命名的文件，
        表明子进程结束
        '''
        if pid == '':
            pid = os.getpid()
        pidfile_path = LOG_PATH + 'engine_pids/' + str(pid)
        if os.path.exists(pidfile_path):
            os.remove(pidfile_path)

    @staticmethod
    def kill_child_process(pid=''):
        '''
        杀掉当前进程，若成功则删除该子进程在/engine_pids目录下文件
        '''
        if pid == '':
            pid = os.getpid()
        pidfile_path = LOG_PATH + 'engine_pids/' + str(pid)
        kill_result = _Daemonize.kill_process(str(pid), pidfile_path)
        if kill_result is True and os.path.exists(pidfile_path):
            os.remove(pidfile_path)
        return kill_result

    def start_operation(self):
        '''
        守护进程启动后运行，需重写为守护进程启动后执行的程序
        '''
        pass

    def stop_operation(self):
        '''
        守护进程结束前运行，需重写为守护进程结束前执行的程序
        '''
        pass


def child_process_run_deco(process_info_name):
    '''
    装饰multiprocessing创建的子进程的run函数，进行子进程存活状态记录
    process_info_name: 子进程中属性名, 属性为在/engine_pids目录下文件中记录的信息, 一般为该进程对应任务信息
    '''
    def _deco(func):
        def __deco(self, *args):
            _Daemonize.write_process_pid(getattr(self, process_info_name))
            func(self, *args)
            _Daemonize.remove_process_pid()
        return __deco
    return _deco

if __name__ is '__main__':
    pass
