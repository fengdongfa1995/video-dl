"""Spider for ixigua.com"""
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

from video_dl.extractor import Extractor
from video_dl.spider import Spider
from video_dl.toolbox import info
from video_dl.video import Media


def add_params(url: str, **params) -> str:
    """add parameters into url"""
    parse_result = urlparse(url)
    query_dict = dict(parse_qsl(parse_result.query))
    query_dict.update(params)

    parse_result = list(parse_result)
    parse_result[4] = urlencode(query_dict)
    return urlunparse(parse_result)

class IXiGuaSpider(Spider):
    """spider for ixigua.com"""
    site = 'ixigua.com'
    home_url = 'https://www.ixigua.com'

    async def before_download(self) -> None:
        """extract key information from html source code."""
        # add a parameter wid_try=1 into target_url
        target_url = add_params(self.url, wid_try=1)
        extractor = Extractor.create(target_url)
        info('url', target_url)

        result = urlparse(target_url)
        await self.fetch_html(target_url)
        meta_data = {
            'pathname': result.path,
            'href': target_url,
            'search': f'?{result.query}' if result.query else '',
            'referrer': target_url,
            'ac_nonce': self.session.cookie_jar.filter_cookies(target_url)['__ac_nonce'].value,
        }
        cookies = extractor.get_cookies(meta_data)
        resp, _ = await self.fetch_html(target_url, cookies=cookies)

        video = self.create_video()
        video.title = extractor.get_title(resp)

        for mp4 in extractor.get_mp4_video_url(resp):
            video.add_media(Media(**mp4))
        self.video_list.append(video)

        if self.lists:
            info('list', 'not implemented yet!')