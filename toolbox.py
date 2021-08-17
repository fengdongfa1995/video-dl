"""toolbox which provides lots of helper function.

class UserAgent deals with user agent.
class Config deals with config information.

Avaliable function:
    UserAgent().random: get a random user agent.
    Config().get_cookie(site): get a site's cookie.
    Configi().something: get the value combined to the key 'something'.

Typical usage example:
    random_ua = UserAgent().random

    config = Config()
    bilibili_cookie = config.get_cookie('bilibili')
    threshold = config.big_file_threshold
"""
from typing import Union
import json
import os
import random


class UserAgent(object):
    """user agent.

    Attributes:
        random: get a random user agent.
    """

    def __init__(self, file_path: str = None):
        """read user agent list from a txt file.

        Args:
            file_path: txt file path, default: ./resource/user_agents.txt.
        """
        if file_path is None:
            file_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'resource', 'user_agents.txt'
            )

        with open(file_path, 'r', encoding='utf-8') as f:
            self.user_agents = [line.strip()
                                for line in f.readlines() if line.strip()]

    @property
    def random(self) -> str:
        """return a random user agent"""
        return random.choice(self.user_agents)


class Config(object):
    """read, parse and return config information."""

    def __init__(self, file_path: str = None):
        """read config information from a json file.

        Args:
            file_path: json file path, default: ./config.json
        """
        if file_path is None:
            file_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'config.json'
            )

        with open(file_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

    def cookie(self, site: str) -> str:
        """return site's cookie.

        Args:
            site: target site.

        Returns:
            target site's cookie. return empty string if no value is avaliable.
        """
        return self.config['cookie'].get(site, '')

    def __getattr__(self, key: str) -> Union[str, int]:
        """return config information specified by key.

        Args:
            key: key.

        Returns:
            config information specified by key.
        """
        value = self.config[key]
        setattr(self, key, value)
        return value
