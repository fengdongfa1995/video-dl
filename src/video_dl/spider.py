"""Base class for Spiders"""
from urllib.parse import urlparse
import aiohttp

from video_dl.args import Arguments
from video_dl.toolbox import UserAgent, info


class Spider(object):
    """crawl data from web and download video."""
    site = 'f-df.com'
    home_url = 'https://f-df.com'

    # all arguments provied by user and config file
    arg = Arguments()
    cookie = arg.cookie
    proxy = arg.proxy
    diretory = arg.directory
    url = arg.url
    interactive = arg.interactive

    @classmethod
    def create_spider(cls, url: str):
        """create a specific subclass depends on url."""
        netloc = urlparse(url).netloc
        for subclass in cls.__subclasses__():
            if subclass.site in netloc:
                return subclass()
        raise NotImplementedError

    def __init__(self):
        self.session = None
        self.headers = {
            'user-agent': UserAgent().random,
            'cookie': self.cookie,
            'referer': self.home_url,
            'origin': self.home_url,
            'accept': '*/*',
        }

        # list of Videos
        self.video_list = []

    async def create_session(self) -> None:
        if self.session is None:
            self.session = aiohttp.ClientSession(headers=self.headers)

    async def close_session(self) -> None:
        if self.session:
            await self.session.close()

    async def fetch_html(self, url: str) -> str:
        """get url's html source code from internet."""
        async with self.session.get(url=url, proxy=self.proxy) as r:
            return await r.text()

    async def before_download(self) -> None:
        """do something before download"""
        raise NotImplementedError

    async def downloading(self) -> None:
        """download video from web."""
        for video in self.video_list:
            await video.download()

    def after_downloaded(self) -> None:
        """do something after downloaded video."""
        pass

    async def run(self) -> None:
        """start crawl."""
        info('site', self.site)
        await self.create_session()

        await self.before_download()
        await self.downloading()
        self.after_downloaded()

        await self.close_session()


# import subclasses of spider
import video_dl.sites  # pylint: disable=import-error
