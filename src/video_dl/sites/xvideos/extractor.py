"""extract information from html source code of pornhub.com."""
import re

from video_dl.extractor import Extractor


class XVideosExtractor(Extractor):
    """xvideos information extractor."""
    pattern = [
        re.compile(r'xvideos.com/video\d+'),
    ]

    # re patterns to extract information from html source code
    re_title = re.compile(r"setVideoTitle\('(.*?)'\)")
    re_video = {
        '1': re.compile(r"setVideoUrlLow\('(.*?)'\);"),
        '2': re.compile(r"setVideoUrlHigh\('(.*?)'\);"),
    }

    def get_title(self, resp: str) -> str:
        """get video's title from html source code."""
        return self.re_title.search(resp).group(1)

    def get_mp4_video(self, resp: str) -> str:
        """xvdeios save its mp4 links in a paired brackets."""
        for key, value in self.re_video.items():
            yield {
                'size': int(key),
                'url': value.search(resp).group(1),
                'desc': 'low' if key == '1' else 'high',
            }
