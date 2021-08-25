"""extract information from html source code of ixigua.com."""
from typing import Optional
import base64
import json
import os
import re
import subprocess

from video_dl.extractor import Extractor


class IXiGuaExtractor(Extractor):
    """ixigua information extractor."""
    pattern = [
        re.compile(r'www.ixigua.com/\d+'),
    ]

    # re patterns to extract information from html source code
    re_video = re.compile(r'window\._SSR_HYDRATED_DATA=(.*?)</script>', re.S)

    def __init__(self, js_path:Optional[str] = None):
        super().__init__()

        if not js_path:
            js_path = os.path.join(os.path.dirname(__file__), '..', '..', 'resource', 'ixigua_acrawler.js')
        self.js_path = js_path

        with open(js_path, 'r', encoding='utf-8') as f:
            self.js_code = f.read()

    def get_cookies(self, meta_data: dict) -> dict:
        for key, value in meta_data.items():
            self.js_code = self.js_code.replace(f'@{key}@', value)
        js_path = os.path.splitext(self.js_path)[0] + '.tmp.js'

        with open(js_path, 'w', encoding='utf-8') as f:
            f.write(self.js_code)
        result = subprocess.run(['node', js_path], stdout=subprocess.PIPE, check=True)

        os.remove(js_path)
        return {
            '__ac_nonce': meta_data['ac_nonce'],
            '__ac_signature': result.stdout.decode('utf-8').strip(),
            '__ac_referer': '__ac_blank',
        }

    def get_title(self, resp: str) -> str:
        """get video's title from html source code."""
        json_string = self.re_video.search(resp).group(1)
        json_string = json_string.replace('undefined', 'null')
        video = json.loads(json_string)
        return video['anyVideo']['gidInformation']['packerData']['video']['title']

    def get_mp4_video_url(self, resp: str) -> list:
        """ixigua.com save its mp4 links in this dictionary."""
        json_string = self.re_video.search(resp).group(1)
        json_string = json_string.replace('undefined', 'null')
        video = json.loads(json_string)

        video_list = video['anyVideo']['gidInformation']['packerData']['video']['videoResource']['normal']['video_list']
        for item in video_list.values():
            yield {
                'url': base64.b64decode(item['main_url']).decode('utf-8'),
                'size': item['size'],
                'desc': item['definition']
            }