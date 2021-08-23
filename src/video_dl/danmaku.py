"""parse danmaku."""
from typing import Optional
import os


class Danmaku(object):
    """Danmaku."""
    def __init__(self, ass_file_path: Optional[str] = None):
        """read ass header from disk."""
        if not ass_file_path:
            ass_file_path = os.path.join(
                os.path.dirname(__file__), 'resource', 'ass_header.txt')

        with open(ass_file_path, 'r', encoding='utf-8') as f:
            self.ass_header = f.read()

        self.subtitles = []

    def edit_header(self, title: str, width: str, height: str) -> None:
        """edit ass header according to title and screen's resolution."""
        self.ass_header = self.ass_header.replace('@title@', title)
        self.ass_header = self.ass_header.replace('@width@', str(width))
        self.ass_header = self.ass_header.replace('@height@', str(height))

        self.subtitles.append(self.ass_header)

    def add_dialog(self, dialog: str) -> None:
        """add a dialogue into subtitles."""
        self.subtitles.append(dialog)

    def output_subtitle(self) -> str:
        """return subtitle."""
        return '\n'.join(self.subtitles)
