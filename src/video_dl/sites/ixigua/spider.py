"""Spider for ixigua.com"""
from urllib.parse import urlparse, urljoin

from video_dl.extractor import Extractor
from video_dl.spider import Spider
from video_dl.toolbox import info
from video_dl.video import Media


class IXiGuaSpider(Spider):
    """spider for ixigua.com"""
    site = 'ixigua.com'
    home_url = 'https://www.ixigua.com'

    def __init__(self):
        super().__init__()

        self.cookies = None

    async def before_download(self) -> None:
        await self.parse_html(self.url)

    async def parse_html(self, target_url: str) -> None:
        """extract key information from html source code.

        Args:
            target_url: target url copied from online vide website.
        """
        info('url', target_url)
        target_url = urljoin(target_url, '?wid_try=1')
        extractor = Extractor.create(target_url)

        # Anti-anti-crawler
        if not self.cookies:
            await self.fetch_html(target_url)
            result = urlparse(target_url)
            meta_data = {
                'pathname': result.path,
                'href': target_url,
                'search': f'?{result.query}' if result.query else '',
                'referrer': target_url,
                'ac_nonce': self.session.cookie_jar.filter_cookies(target_url)['__ac_nonce'].value,
            }
            self.cookies = extractor.get_cookies(meta_data)

        resp, _ = await self.fetch_html(target_url, cookies=self.cookies)
        video = self.create_video()
        video.title = extractor.get_title(resp)

        for mp4 in extractor.get_mp4_video_url(resp):
            video.add_media(Media(**mp4))
        self.video_list.append(video)

        if self.lists:
            info('list', 'not implemented yet!')