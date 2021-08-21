"""extract information from html source code of bilibili.com."""
from urllib.parse import urljoin
import json
import re

from video_dl.extractor import Extractor


class BilibiliVideoExtractor(Extractor):
    """bilibili information extractor."""
    pattern = [
        re.compile('bilibili.com/video/BV.*'),
    ]

    # re patterns to extract information from html source code
    re_state = re.compile(r'__INITIAL_STATE__=(.*?);\(function\(\)')
    re_playinfo = re.compile(r'window.__playinfo__=(.*?)</script>')

    def __init__(self):
        self.id2desc = None

    def get_title(self, resp: str) -> str:
        """get video's title from html source code."""
        state = json.loads(self.re_state.search(resp).group(1))

        current_page = state['p']
        pages = state['videoData']['pages']

        if len(pages) == 1:
            return state['videoData']['title']

        for page in pages:
            if page['page'] == current_page:
                return page['part']

    def get_parent_folder(self, resp: str) -> str:
        """get video's parent folder from html source code."""
        state = json.loads(self.re_state.search(resp).group(1))

        pages = state['videoData']['pages']
        if len(pages) > 1:
            return state['videoData']['title']
        else:
            return None

    def get_pictures(self, resp: str) -> list:
        """get pictures' information from html source code."""
        playinfo = json.loads(self.re_playinfo.search(resp).group(1))

        if self.id2desc is None:
            desc = playinfo['data']['accept_description']
            quality = playinfo['data']['accept_quality']
            self.id2desc = {
                str(key): value for key, value in zip(quality, desc)
            }

        pictures = playinfo['data']['dash']['video']
        for media in pictures:
            yield {
                'url': media['base_url'],
                'size': media['bandwidth'],
                'desc': f"{self.id2desc[str(media['id'])]} + {media['codecs']}"
            }

    def get_sounds(self, resp: str) -> list:
        """get sounds' information from html source code."""
        playinfo = json.loads(self.re_playinfo.search(resp).group(1))

        if self.id2desc is None:
            desc = playinfo['data']['accept_description']
            quality = playinfo['data']['accept_quality']
            self.id2desc = {
                str(key): value for key, value in zip(quality, desc)
            }

        sounds = playinfo['data']['dash']['audio']
        for media in sounds:
            yield {
                'url': media['base_url'],
                'size': media['bandwidth'],
            }

    def generate_urls(self, resp: str, base_url: str) -> list:
        """generate urls from html resource code."""
        state = json.loads(self.re_state.search(resp).group(1))

        current_page = state['p']
        pages = state['videoData']['pages']
        for page in pages:
            if (index := page['page']) != current_page:
                yield urljoin(base_url, f'?p={index}')


class BilibiliBangumiExtractor(BilibiliVideoExtractor, Extractor):
    """extractor for bilibili bangumi"""
    pattern = [
        re.compile('bilibili.com/bangumi/play/ep.*'),
        re.compile('bilibili.com/bangumi/play/ss.*'),
    ]

    def get_title(self, resp: str) -> str:
        """get video's title from html source code."""
        state = json.loads(self.re_state.search(resp).group(1))
        return state['h1Title']

    def get_parent_folder(self, resp: str) -> str:
        """get video's parent folder from html source code."""
        state = json.loads(self.re_state.search(resp).group(1))
        return state['mediaInfo']['season_title']

    def generate_urls(self, resp: str, base_url: str) -> list:
        """generate urls from html resource code."""
        state = json.loads(self.re_state.search(resp).group(1))

        pages = state['mediaInfo']['episodes']
        for page in pages:
            url = page['link'].replace('/u002f', '/')
            if url not in base_url:
                yield url
