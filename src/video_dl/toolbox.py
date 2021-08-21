"""toolbox which provides lots of helper function.

class UserAgent deals with user agent.

Avaliable function:
    UserAgent().random: get a random user agent.
    info: print prompt message.
    ask_user: ask user to provide a string of numbers.

Typical usage:
    random_ua = UserAgent().random
    info('url', 'https://www.bilibili.com/video/xxx')
    video_index, audio_index = ask_user(count=2, default=1)
"""
from typing import Optional
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


class ConsoleColor(object):
    """ANSI control code for color."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def info(label: str, *args, **kwargs) -> None:
    """print information to console with colors."""
    print(f'{ConsoleColor.WARNING}[{label}]{ConsoleColor.OKGREEN}',
          *args, ConsoleColor.ENDC, **kwargs)


def ask_user(count: Optional[int] = 2, default: Optional[int] = 1) -> tuple:
    """ask user to provide answers.

    Args:
        count: count of required answer.
        default: default value.
    """
    prompt = ('What is your answer(space to separate, enter to use default: '
              f'{default}):')
    answer = input(prompt).strip()
    if not answer:
        result = (default, ) * count
    else:
        result = tuple(int(item) for item in answer.split(' '))

    if len(result) == 1:
        return result[0]
    else:
        return result
