# -*- coding: utf-8 -*-

'''
Name: mongo集合定义(基于mongoengine)
Author：XinYi 609610350@qq.com
Time：2015.5.10
'''

from errors import DependencyNotInstalledError

try:
    from mongoengine import Document, EmbeddedDocument, \
        StringField, DateTimeField, EmailField, \
        BooleanField, URLField, IntField, FloatField, \
        ListField, EmbeddedDocumentField, DictField, \
        ObjectIdField
except ImportError:
    raise DependencyNotInstalledError('mongoengine')


class UrlList(Document):  # 存储URL列表
    list_name = StringField()  # 列表名称
    list_type = StringField()  # 类型：‘手动’，‘域名探测’，‘关键字探测‘ 等
    creat_time = StringField()  # 生成时间
    update_time = StringField()  # 更新时间
    usr_id = IntField()  # 用户ID
    task_id = IntField()  # 任务ID
    list_num = IntField()  # 列表中URL数量
    use_count = IntField()  # 使用次数
    urls = ListField(StringField())  # URL列表
    child_list = ListField(ObjectIdField())  # 该列表对应所有子列表objectID列表