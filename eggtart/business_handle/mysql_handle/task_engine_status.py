# -*- coding: utf-8 -*-
'''
Name: task_engine_status 表操作方法
Author：
Time：2016.7.28
'''

import sys
import os

present_path = os.path.abspath('.').split('/')[:-2]
sys.path.append('/'.join(present_path) + '/server_base')
from utils import transfer_time_reformat


TableFieldDescripe = {'task_id': 's', 'engine_type': 's', 'start_time': 's', 'engine_id': 's','win_url_num': 'd', 'error_url_num': 'd', 'error_urls': 's', 'over_time': 's', 'run_time': 'd'}


def into_task_engine_status(mysql_handle_base, job_body):
    '''
    填写task_engine_status数据表
    '''
    table_field_descripe = TableFieldDescripe
    for engine_status in job_body['run_state']:
        update_fields = {'task_id': [job_body['task_id'], 's']}
        # 得到引擎名称及其代号
        single_engine_name_temp = engine_status.keys()[0]
        engine_name = single_engine_name_temp[
            0:single_engine_name_temp.find('conf') - 1]
        # 存储engine_type、engine_id、over_time、start_time四个字段信息
        for once_status in engine_status:
            engine_attribute = once_status[once_status.find('yaml_') + 5:]
            if engine_attribute in table_field_descripe:
                update_fields[engine_attribute] = [
                    engine_status[once_status], 's']
        # 得到类似web_save_status格式的字段
        engine_run_status = engine_name + '_status'
        update_fields['error_urls'] = [[], 's']
        update_fields['win_url_num'] = [0, 'd']
        update_fields['error_url_num'] = [0, 'd']
        # 存储error_urls、win_url_num、error_url_num三个字段
        for once_task in job_body['task_list']:
            task_keys = once_task.keys()
            if engine_run_status in task_keys:
                if once_task[engine_run_status] == True:
                    update_fields['win_url_num'][0] += 1
                elif once_task[engine_run_status] == False:
                    update_fields['error_url_num'][0] += 1
                    update_fields['error_urls'][0].append(once_task['url'])
        # 计算运行时间
        if 'start_time' in update_fields and 'over_time' in update_fields:
            update_fields['run_time'] = [int(transfer_time_reformat(update_fields['over_time'][
                                             0]) - transfer_time_reformat(update_fields['start_time'][0])), 'd']
        task_id = job_body['task_id']
        engine_type = update_fields['engine_type'][0]
        select_resule = mysql_handle_base.select('task_engine_status', fields=['task_id'], wheres={
            'task_id': [task_id, 's'], 'engine_type': [engine_type, 's']}, fetch_type='one')
        if select_resule == False:
            result = mysql_handle_base.insert(
                'task_engine_status', update_fields)
        else:
            wheres = {'task_id': [job_body['task_id'],
                                  's'], 'engine_type': [engine_type, 's']}
            result = mysql_handle_base.update(
                'task_engine_status', update_fields, wheres)

            
if __name__ == '__main__':
    from mysql_handle_base import MysqlHandleBase
    mysql_handle = MysqlScheduler(mysql_host='127.0.0.1', mysql_db='test',  mysql_user='root',  mysql_password='zxy')
    job_body = open('1469843362_66.json')
    job_body = json.load(job_body)
    into_gray_engine_result(mysql_handle_base, job_body)

