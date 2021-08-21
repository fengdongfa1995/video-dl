"""read config from config file and user's input, then return the result.

Typical usage:
    args = Arguments()
    cookie = args.cookie
    url = args.url

Available arguments:
    big_file_threshold: file size exceeds this threshold will be sliced.
    chunk_size: chunk size to read from stream.
    cookie: user's own cookie.
    directory: set a target directory to save video.
    interactive: choose media resource manually.
    lists: try to find a playlist and download all video contained in it.
    max_conn: maximum connections simultaneously.
    proxy: internet proxy.
    url: target url.
"""
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
        # set config file's absolute path
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
            epilog=('You could find more important information in '
                    '[github](https://github.com/fengdongfa1995/video_dl).'),
        )

        # flags
        parser.add_argument(
            '-i', '--interactive', action='store_true',
            help='Manually select download resources.',
        )

        parser.add_argument(
            '-l', '--lists', action='store_true',
            help='try to find a playlist and download all videos in it.',
        )

        # something provided by user
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

        # required arguments
        parser.add_argument(
            'url', help='target url copied from online video website.',
        )

        # program's version
        parser.add_argument('-v', '--version',
                            action='version', version=f'%(prog)s {version}')

        # command line arguments parser result
        args = parser.parse_args()
        self.args = vars(args)


class Arguments(object):
    """provide global variables to other modules."""
    args = ArgParse().args  # arguments provided by user
    config = Config().config  # auguments provided by config file

    def _if_none_return_empty_string(self, key: str) -> str:
        """if value of the key is None, the return ''."""
        # just find key in self.args
        # because config file have no key point to None
        return '' if self.args[key] is None else self.args[key]

    @property
    def cookie(self) -> str:
        """
        if user doesn't set a cookie, cookie will be None.
        but our program need a empty string not the None.
        """
        return self._if_none_return_empty_string('cookie')

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

        setattr(self, key, value)
        return value
