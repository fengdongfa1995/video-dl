"""extract information from html source code of bilibili.com."""
from urllib.parse import urljoin
import json
import os
import re

from google.protobuf.json_format import MessageToJson
import execjs

from video_dl.sites.bilibili.dm_pb2 import DmSegMobileReply
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

        # ready to use javascript code
        with open(os.path.join(
            os.path.dirname(__file__), '..', '..',
            'resource', 'bilibili_sub.js'
        )) as f:
            self.js_code = execjs.compile(f.read())

    def jsonsub_to_asssub(self, title: str, sub_list: list) -> str:
        """json substitle to ass substitle."""
        try:
            return self.js_code.call('xmlDanmakus', title, sub_list)
        except Exception:  # pylint: disable=W0703
            return ''

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

    def get_oid_pid(self, resp: str, base_url: str = None) -> tuple:
        """get oid and pid from html source code."""
        del base_url
        state = json.loads(self.re_state.search(resp).group(1))
        oid = state['videoData']['cid']
        pid = state['aid']
        return oid, pid

    def get_dm(self, bytes_stream: str) -> dict:
        """generate json dictionary from binary stream."""
        dm = DmSegMobileReply()
        dm.ParseFromString(bytes_stream)
        return json.loads(MessageToJson(dm))


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

    def get_oid_pid(self, resp: str, base_url: str) -> tuple:
        """get oid and pid from html source code."""
        state = json.loads(self.re_state.search(resp).group(1))
        pages = state['mediaInfo']['episodes']
        for page in pages:
            url = page['link'].replace('/u002f', '/')
            if url in base_url:
                oid = page['cid']
                pid = page['aid']
                return oid, pid
