"""extract information from html source code of pornhub.com."""
import json
import re

from video_dl.extractor import Extractor


class PornhubExtractor(Extractor):
    """pornhub information extractor."""
    pattern = [
        re.compile(r'pornhub.com/view_video.php\?viewkey='),
    ]

    # re patterns to extract information from html source code
    re_video_show = re.compile(r'VIDEO_SHOW.*?({.*?});')
    re_mp4_url = re.compile(r'player_mp4_seek.*?//.*?;(.*?);flashvars', re.S)
    re_key_value = re.compile('var (.*?)=(.*)')
    re_drop_char = re.compile('[ +"]')

    def get_title(self, resp: str) -> str:
        """get video's title from html source code."""
        video_show = json.loads(self.re_video_show.search(resp).group(1))
        return video_show['videoTitle']

    def get_mp4_video_url(self, resp: str) -> str:
        """pornhub save its mp4 links in this url."""
        url_string = self.re_mp4_url.search(resp).group(1)
        url_string = re.sub(r'/\*.*?\*/', '', url_string)  # drop comment
        url_string = re.sub(r'[\n\t]', '', url_string)  # drop extra space

        result = {}
        url = []
        for item in url_string.split(';'):
            key, value = self.re_key_value.search(item).groups()
            if key != 'media_0':  # get tamporary variables
                result[key] = self.re_drop_char.sub('', value)
            else:
                for k in value.split('+'):  # ger final url
                    url.append(result[k.strip()])
        return ''.join(url)
