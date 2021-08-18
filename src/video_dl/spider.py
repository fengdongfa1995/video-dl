"""Base class for Spiders"""
import aiohttp

from video_dl.args import Arguments
from video_dl.toolbox import UserAgent


class Spider(object):
    """crawl data from web and download video."""
    site = 'f-df.com'
    home_url = 'https://f-df.com'

    # everything provied by user and config file
    arg = Arguments()
    cookie = arg.cookie
    proxy = arg.proxy
    diretory = arg.directory
    target_url = arg.url
    interactive = arg.interactive

    def __init__(self):
        self.session = None

    async def create_session(self) -> None:
        if self.session is None:
            headers = {
                'user-agent': UserAgent().random,
                'cookie': self.cookie,
                'referer': self.home_url,
                'origin': self.home_url,
                'accept': '*/*',
            }
            self.session = aiohttp.ClientSession(headers=headers)

    async def close_session(self) -> None:
        if self.session:
            await self.session.close()

    async def fetch_html(self, url: str) -> str:
        """get url's html source code from internet."""
        async with self.session.get(url=url, proxy=self.proxy) as r:
            return await r.text()

    async def parse_html(self, url: str) -> None:
        """Extract data from html source code."""
        raise NotImplementedError
