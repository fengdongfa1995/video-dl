"""convert json subtitles to ass subtitles."""
import random

from video_dl.danmaku import Danmaku


class Convertor(object):
    """convert json to ass."""
    def __init__(self, file_path: str = None):
        self.danmaku = Danmaku(file_path)
        self.screen_width = 560  # width of screen
        self.screen_height = 420  # height of screen
        self.move_time = 8  # duration time of move subtitle
        self.fixed_time = 4  # duration time of fixed subtitle

        self.result = []

    def edit_header(self, title: str) -> None:
        self.danmaku.edit_header(title, self.screen_width, self.screen_height)

    def ms2datetime(self, ms: int) -> str:
        """convert ms to datetime."""
        hour = int(ms/(1000*60*60))
        minute = int(ms/(1000*60)) % 60
        second = int(ms/1000) % 60
        ms = ms % 1000

        return f'{hour}:{minute}:{second}.{ms}'

    def json2ass(self, danmaku_list: dict) -> None:
        for json_data in danmaku_list:
            random_height = random.randint(0, self.screen_height)
            try:
                text = json_data['content']
                content_len = 12 * len(text)

                if json_data['mode'] in (1, 2, 3, 7, 8, 9):
                    duration = self.move_time * 1000
                    move = (r'\an7\move('
                            f'{self.screen_width}, {random_height},'
                            f' {-content_len}, {random_height})')
                elif json_data['mode'] == 6:
                    duration = self.move_time * 1000
                    move = (r'\an9\move('
                            f'0, {random_height}, '
                            f'{content_len+self.screen_width}, '
                            f'{random_height})')
                elif json_data['mode'] == 4:  # bottom
                    duration = self.fixed_time * 1000
                    move = (r'\an2\pos('
                            f'{self.screen_width/2}, {self.screen_height})')
                elif json_data['mode'] == 5:  # top
                    duration = self.fixed_time * 1000
                    move = (r'\an8\pos('
                            f'{self.screen_width/2},'
                            ' {random_height})')

                color = r'\c&H' + str(hex(json_data['color']))[-6:] + '&'
                code = f'{{{move}{color}}}'

                start = self.ms2datetime(json_data['progress'])
                end = self.ms2datetime(json_data['progress'] + duration)

                self.result.append(
                    f'Dialogue: 0,{start},{end},Danmaku,,0,0,0,,{code}{text}'
                )
            except Exception:  # pylint: disable=W0703
                continue

    def output(self) -> str:
        return self.danmaku.output_subtitle()
