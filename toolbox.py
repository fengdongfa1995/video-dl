"""公用函数库

主要功能：
    - USERAGENT.random提供随机UA
"""
import json
import os
import random


class UserAgent(object):
    """UserAgent类

    主要功能：
        - 通过UserAgent().random提供随机UA
    """
    def __init__(self, file_path: str = None):
        # 读取user_agents文件
        if file_path is None:
            file_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'resource/user_agents.txt'
            )

        self.user_agents = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                self.user_agents.append(line.strip())

    @property
    def random(self) -> str:
        """随机抽取一个ua"""
        return random.choice(self.user_agents)


class Config(object):
    """配置文件类

    主要功能：

    """
    def __init__(self, file_path: str = None):
        # 读取配置文件
        if file_path is None:
            file_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'config.json'
            )

        with open(file_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

    def cookie(self, site: str) -> str:
        """随机抽取一个ua

        @param site: 目标网站

        @return: 目标网站的cookie
        """
        return self.config['cookie'].get(site, '')

    def __getattr__(self, key: str):
        """返回配置文件当中的配置信息

        @param key: 键
        """
        value = self.config[key]
        setattr(self, key, value)
        return value


USERAGENT = UserAgent()
CONFIG = Config()
