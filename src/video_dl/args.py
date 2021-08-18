"""read config from config file and user's input."""
from typing import Any
import argparse
import json
import os

from video_dl import __version__ as version


class Config(object):
    """read, parse and return config information."""

    def __init__(self, file_path: str = None):
        """read config information from a json file.

        Args:
            file_path: json file path, default: resource/config.json
        """
        if file_path is None:
            file_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'resource', 'config.json'
            )

        with open(file_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)


class ArgParse(object):
    """parse command line arguments with argparse."""
    def __init__(self):
        parser = argparse.ArgumentParser(
            prog='video_dl',
            description='A naive online video downloader based on aiohttp',
            epilog=('You could find more important information from '
                    '[github](https://github.com/fengdongfa1995/video_dl).'),
        )

        parser.add_argument(
            '-i', '--interactive', action='store_true',
            help='Manually select download resources.',
        )

        parser.add_argument(
            '-l', '--list', action='store_true',
            help='try to find a playlist and download.',
        )

        parser.add_argument(
            'url', help='target url copied from online video website.',
        )

        parser.add_argument(
            '-d', '--directory',
            help='set target diretory to save video file(s).',
        )

        parser.add_argument(
            '-c', '--cookie',
            help='provide your cookie.',
        )

        parser.add_argument(
            '-p', '--proxy',
            help='set proxy. e.g.: http://127.0.0.1:10809',
        )

        parser.add_argument('-v', '--version',
                            action='version', version=f'%(prog)s {version}')

        # command line arguments parser result
        args = parser.parse_args()
        self.args = vars(args)


class Arguments(object):
    """provide global variables to other modules."""
    args = ArgParse().args  # arguments provided by user
    config = Config().config  # auguments provided by config file

    def __init__(self):
        pass

    def _if_none_return_empty(self, key: str):
        return '' if self.args[key] is None else self.args[key]

    @property
    def cookie(self):
        return self._if_none_return_empty('cookie')

    def __getattr__(self, key: str) -> Any:
        if key not in self.args and key not in self.config:
            raise KeyError
        elif key not in self.args and key in self.config:
            value = self.config[key]
        elif key in self.args and key not in self.config:
            value = self.args[key]
        elif key in self.args and key in self.config:
            if self.args[key] is None:
                value = self.config[key]
            else:
                value = self.args[key]
        else:
            raise NotImplementedError

        setattr(self, key, value)
        return value
