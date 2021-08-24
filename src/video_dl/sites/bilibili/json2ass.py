"""convert json subtitles to ass subtitles."""
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
        self.danmaku.edit_header(title)

    def ms2datetime(self, ms: int) -> str:
        """convert ms to datetime."""
        hour = int(ms/(1000*60*60))
        minute = int(ms/(1000*60)) % 60
        second = int(ms/1000) % 60
        ms = ms % 1000

        return f'{hour}:{minute}:{second}.{ms}'

    def json2ass(self, json_data: dict) -> None:
        text = json_data['content']

        if json_data['mode'] in (1, 2, 3, 7, 8, 9):
            duration = self.move_time * 1000
            mode = 'normal'
        elif json_data['mode'] == 6:
            duration = self.move_time * 1000
            mode = 'reverse'
        elif json_data['mode'] == 4:  # bottom
            duration = self.fixed_time * 1000
            mode = 'bottom'
        elif json_data['mode'] == 5:  # top
            duration = self.fixed_time * 1000
            mode = 'top'

        start = self.ms2datetime(json_data['progress'])
        end = self.ms2datetime(json_data['progress'] + duration)
        color = r'\c&H' + str(hex(json_data['color']))[-6:] + '&'

        self.danmaku.add_dialog(self.danmaku.generate_dialog(**{
            'start': start,
            'end': end,
            'mode': mode,
            'content': text,
            'color': color,
        }))

    def output(self) -> str:
        return self.danmaku.output_subtitle()
