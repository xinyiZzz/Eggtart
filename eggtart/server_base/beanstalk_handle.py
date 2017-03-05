#!/usr/bin/python
#-*-coding:utf-8-*-

'''
Name: beanstalk操作模块，提供put和get方法  https://github.com/xinyi-spark/MiniORM-beanstalk
Author：XinYi 609610350@qq.com
Time：2016.4
'''

import os
import sys
import traceback
import json
import beanstalkc
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s-[%(asctime)s][%(module)s][%(funcName)s][%(lineno)d]: %(message)s')


class BeanstalkHandle():

    def __init__(self, host='127.0.0.1', port=11300):
        self.host = host
        self.port = port
        # self.bean = self.connect_beanstalk()  # (弃用，不稳定)相当于全局连接对象，在put中多次调用

    def __del__(self):
        '''
        断开beanstalk连接
        '''
        pass
        # self.bean.close()

    def connect_beanstalk(self):
        '''
        连接beanstalk
        '''
        try:
            bean = beanstalkc.Connection(self.host, self.port)
            # logger.debug('connect beanstalk win, ip: %s' % self.host)
            return bean
        except:
            logger.error('Can not connect to beanstalk: %s' % self.host)
            raise

    def check_error(self, e):
        '''
        连接beanstalk服务器超时，则重新连接
        '''
        try:
            if str(e) == '[Errno 32] Broken pipe' or str(e) == '[Errno 104] Connection reset by peer':  # 说明连接MySQL服务器超时等
                # self.bean = self.connect_beanstalk()
                return True
            else:
                return False
        except:
            return False

    def _decode_dict(self, data):
        '''
        递归对字典中所有元素编码为utf-8
        '''
        rv = {}
        for key, value in data.iteritems():
            if isinstance(key, unicode):
                key = key.encode('utf-8')
            if isinstance(value, unicode):
                value = value.encode('utf-8')
            elif isinstance(value, list):
                pass
            elif isinstance(value, dict):
                value = self._decode_dict(value)
            rv[key] = value
        return rv

    def put(self, tube, data):
        '''
        将一组数据put到指定队列中
        tube：指定队列
        data: {'save_task': finish_task_list}
        '''
        try:
            bean = self.connect_beanstalk()
            bean.use(tube)
            bean.put(json.dumps(data))
        except beanstalkc.SocketError, e:
            re_connect_result = self.check_error(e)
            if re_connect_result is True:
                return self.put(tube, data)
            else:
                raise
        except:
            logger.debug('put tube error: %s, data: %s' % (tube, data))
            raise
        logger.debug('put tube: %s, data: %s' % (tube, data))
        return True

    def get(self, tube, infinite_loop=True, num=1):
        '''
        循环监听指定队列，并通过迭代器返回取得的消息
        tube：指定队列
        infinite_loop：是否无限循环监听
        num: 当有限循环监听时，设置接收消息个数
        '''
        local_bean = self.connect_beanstalk()  # 每次get时都新建链接，不使用全局连接，防止监听混乱
        local_bean.watch(tube)
        local_bean.ignore('default')
        while True:
            try:
                job_msg = local_bean.reserve(timeout=60)
                assert job_msg
            except:
                if job_msg is not None:
                    logger.debug('job_msg reserve error %s' % (job_msg, ))
                continue
            try:
                job_body = json.loads(
                    job_msg.body, object_hook=self._decode_dict)
                job_msg.bury()
                yield job_msg, job_body
            except GeneratorExit:  # 说明迭代结束，抛出该异常通知外部调用循环
                raise
            except:
                traceback.print_exc()
                continue
            finally:
                try:
                    job_msg.delete()
                except beanstalkc.CommandFailed:
                    logger.error('job_msg del error, body:%s' % (job_body, ))
            if infinite_loop == False:
                num -= 1
                if num == 0:
                    break
        local_bean.close()


if __name__ == '__main__':
    beanstalk_handle = BeanstalkHandle(host='172.31.137.240')
    beanstalk_handle.put('test', {'save_task': ['aaa', 'bbbb']})
    beanstalk_handle.put('test', {'save_task': ['1111', '2222']})
    for job_msg, job_body in beanstalk_handle.get('test', infinite_loop=False, num=2):
        print job_msg, job_body
