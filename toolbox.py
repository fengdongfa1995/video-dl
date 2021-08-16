import json
import os
import random


class UserAgent(object):
    """UserAgent类

    主要功能：
        - UserAgent().random 返回随机UA
    """
    def __init__(self, file_path: str = None):
        """读取存储在文本文件当中的UserAgents列表

        @param file_path: 文本文件存储路径，默认为resource/user_agents.txt
        """
        if file_path is None:
            file_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'resource', 'user_agents.txt'
            )

        self.user_agents = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                if (l := line.strip()):
                    self.user_agents.append(l)

    @property
    def random(self) -> str:
        """随机返回一个UserAgent"""
        return random.choice(self.user_agents)


class Config(object):
    """配置文件类

    主要功能：
        - Config().cookie(site) 返回站点cookie
        - Config().key 返回配置文件中key键对应的内容
    """
    def __init__(self, file_path: str = None):
        """从json文件当中读取配置文件

        @param file_path: 配置文件存储路径，默认为config.json
        """
        if file_path is None:
            file_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'config.json'
            )

        with open(file_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

    def cookie(self, site: str) -> str:
        """返回目标网站的cookie，默认为空字符串

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


# 创建两个模块级别的全局变量，避免反复读取存储在硬盘当中的文本文件
USERAGENT = UserAgent()
CONFIG = Config()
