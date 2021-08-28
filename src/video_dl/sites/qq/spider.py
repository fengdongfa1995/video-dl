"""Spider for v.qq.com"""
from urllib.parse import urlencode
import os
import random
import json
import subprocess
import time

from video_dl.spider import Spider
from video_dl.toolbox import info
from video_dl.video import Media


def create_guid() -> str:
    """create a guid."""
    t = []
    for _ in range(32):
        t.append(str(hex(random.randint(0, 15)))[2:])
    return ''.join(t)

def get_ckey(vid: str, guid: str, tm: str) -> str:
    """get ckey from javascript code."""
    resource_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'resource')
    js_path = os.path.join(resource_dir, 'qq_ckey.js')
    js_tmp_path = os.path.join(resource_dir, 'qq_tmp_ckey.js')

    template_dict = {
        'wasm_path': os.path.join(resource_dir, 'qq_ckey.wasm').replace('\\', '/'),
        'vid': vid,
        'guid': guid,
        'tm': tm,
    }

    with open(js_path, 'r', encoding='utf-8') as raw:
        with open(js_tmp_path, 'w', encoding='utf-8') as f:
            raw_str = raw.read()
            for key, value in template_dict.items():
                raw_str = raw_str.replace(f'@{key}@', value)
            f.write(raw_str)

    result = subprocess.run(['node', js_tmp_path], stdout=subprocess.PIPE, check=True)
    os.remove(js_tmp_path)
    return result.stdout.decode('utf-8').strip()

class QQSpider(Spider):
    """spider for xvideos.com"""
    site = 'v.qq.com'
    home_url = 'https://v.qq.com/'
    post_url = 'https://vd.l.qq.com/proxyhttp'

    login_token = r'&logintoken=%7B%22main_login%22%3A%22%22%2C%22openid%22%3A%22%22%2C%22appid%22%3A%22%22%2C%22access_token%22%3A%22%22%2C%22vuserid%22%3A%22%22%2C%22vusession%22%3A%22%22%7D'

    async def before_download(self) -> None:
        """get video information before downloading video."""
        await self.parse_html(self.url)

    async def parse_html(self, target_url: str) -> None:
        """get video information from target url."""
        info('url', self.url)

        guid = create_guid()
        flowid = create_guid() + '_10201'
        vid = target_url.split('/')[-1].split('.')[0]
        tm = int(time.time())

        vinfoparam = {
            'spsrt': 1,
            'charge': 0,
            'defaultfmt': "auto",
            'otype': "ojson",
            'guid': guid,
            'flowid': flowid,
            'platform': "10201",
            'sdtfrom': "v1010",
            'defnpayver': 1,
            'appVer': '3.5.57',
            'host': 'v.qq.com',
            'ehost': target_url,
            'refer': 'v.qq.com',
            'sphttps': 1,
            'tm': tm,
            'spwm': 4,
            'vid': vid,
            'defn': "fhd",
            'fhdswitch': 0,
            'show1080p': 1,
            'isHLS': 1,
            'dtype': 3,
            'sphls': 2,
            'spgzip': 1,
            'dlver': 2,
            'drm': 32,
            'hdcp': 1,
            'spau': 1,
            'spaudio': 15,
            'defsrc': 1,
            'encryptVer': '9.1',
            'cKey': get_ckey(vid=vid, guid=guid, tm=str(tm)),
            'fp2p': 1,
            'spadseg': 3,
        }
        data = {
            'buid': 'onlyvinfo',
            'vinfoparam': urlencode(vinfoparam) + self.login_token,
        }
        
        resp = await self.fetch_json(url=self.post_url, method='post', json=data)
        json_data = json.loads(resp['vinfo'])
        
        video = self.create_video()
        for desc, item in zip(json_data['fl']['fi'], json_data['vl']['vi'][0]['ul']['ui']):
            print(desc, item)