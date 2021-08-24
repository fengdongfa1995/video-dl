"""parse danmaku."""
from typing import Optional
import os
import random


class Danmaku(object):
    """Danmaku."""
    def __init__(self, ass_file_path: Optional[str] = None):
        """read ass header from disk."""
        if not ass_file_path:
            ass_file_path = os.path.join(
                os.path.dirname(__file__), 'resource', 'ass_header.txt')

        with open(ass_file_path, 'r', encoding='utf-8') as f:
            self.ass_header = f.read()

        self.screen_width = 560
        self.screen_height = 420

        self.subtitles = []

    def edit_header(self, title: str,
                    width: Optional[str] = None,
                    height: Optional[str] = None) -> None:
        """edit ass header according to title and screen's resolution."""
        if not width:
            width = self.screen_width
        else:
            self.screen_width = width

        if not height:
            height = self.screen_height
        else:
            self.screen_height = height

        self.ass_header = self.ass_header.replace('@title@', title)
        self.ass_header = self.ass_header.replace('@width@', str(width))
        self.ass_header = self.ass_header.replace('@height@', str(height))

        self.subtitles.append(self.ass_header)

    # TODO: advanced algorithm
    def generate_dialog(self, start: str, end: str, mode: str, content: str,
                        fontsize: Optional[str] = '',
                        color: Optional[str] = '',
                        ) -> str:
        height = random.randint(0, self.screen_height)
        content_len = 12 * len(content)

        if mode == 'normal':
            move = (r'\an7\move('
                    f'{self.screen_width}, {height},'
                    f' {-content_len}, {height})')
        elif mode == 'reverse':
            move = (r'\an9\move('
                    f'0, {height}, '
                    f'{content_len + self.screen_width}, {height})')
        elif mode == 'bottom':
            move = r'\an2\pos(' + f'{self.screen_width/2}, {height})'
        elif mode == 'top':
            move = r'\an8\pos(' + f'{self.screen_width/2}, {height})'

        code = f'{{{fontsize}{move}{color}}}'
        return f'Dialogue: 0,{start},{end},Danmaku,,0,0,0,,{code}{content}'

    def add_dialog(self, dialog: str) -> None:
        """add a dialogue into subtitles."""
        self.subtitles.append(dialog)

    def output_subtitle(self) -> str:
        """return subtitle."""
        return '\n'.join(self.subtitles)
