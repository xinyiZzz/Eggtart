# -*- coding: utf-8 -*-

'''
Name: yaml配置文件预处理
Author：XinYi 609610350@qq.com
Time：2015.5
'''

from errors import DependencyNotInstalledError

try:
    import yaml
except ImportError:
    raise DependencyNotInstalledError('pyyaml')


class PropertyObject(dict):  # 继承自dict类,此类的实例依然为字典，比dict多了update这个函数

    def __init__(self, d):
        super(PropertyObject, self).__init__()
        self._update(d)

    def _update(self, d):
        for k, v in d.iteritems():
            if not k.startswith('_'):
                self[k] = v

                if isinstance(v, dict):
                    setattr(self, k, PropertyObject(v))
                elif isinstance(v, list):
                    setattr(self, k, [PropertyObject(itm) for itm in v])
                else:
                    setattr(self, k, v)

    def update(self, config=None, **kwargs):
        self._update(kwargs)
        if config is not None:
            if isinstance(config, dict):
                self._update(config)
            else:
                self._update(config.conf)


class Config(object):  # 读取yaml配置文件

    def __init__(self, yaml_file):
        if isinstance(yaml_file, str):
            f = open(yaml_file)
        else:
            f = yaml_file
        try:
            self.conf = PropertyObject(yaml.load(f))
        finally:
            f.close()

        for k, v in self.conf.iteritems():
            if not k.startswith('_'):
                if isinstance(v, dict):
                    v = PropertyObject(v)
                setattr(self, k, v)

    def __getitem__(self, name):
        return getattr(self, name)

if __name__ == '__main__':
    user_config = Config('control_conf.yaml')
    print user_config.server.type
    print user_config.server.server_num
    print user_config.mysql.mysql_host
