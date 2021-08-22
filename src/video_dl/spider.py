"""Base class of all Spiders.

Typical usage:
    url = 'https://www.bilibili.com/video/BV15L411p7M8'
    spider = Spider.create(url)  # will return a BilibiliSpider object
    asycio.run(spider.run())  # try to fetch resource information and download
"""
from urllib.parse import urlparse
import aiohttp
import asyncio

from video_dl.args import Arguments
from video_dl.toolbox import UserAgent, info


class Spider(object):
    """crawl data from web and download video.

    subclass of Spider should provide two public attributes:
        site: this class will use this field to create a specific Spider for
            target url. for example, BilibiliSpider's site is 'bilibili.com',
            will auto match to a url like 'https://www.bilibili.com/video/*'.
        home_url: target website's home page. this field will be inserted into
            headers of session to avoid some `no referer, no download` policy.

    subclass of Spider should implement some public methods:
        before_download: do something before download, just like: parse html.
        after_download: merge picture and sound to a completed video, delete
            tamporary files, and et al..
    """
    arg = Arguments()

    cookie = arg.cookie
    diretory = arg.directory
    proxy = arg.proxy
    url = arg.url
    lists = arg.lists

    @classmethod
    def create(cls, url: str):
        """create a specific subclass depends on url."""
        netloc = urlparse(url).netloc
        for subclass in cls.__subclasses__():
            if subclass.site in netloc:
                return subclass()
        raise NotImplementedError

    def __init__(self):
        self.session = None
        self.headers = {
            'accept': '*/*',
            'user-agent': UserAgent().random,
            'cookie': self.cookie,
            'referer': self.home_url,
            'origin': self.home_url,
        }

        # list that contains Videos
        self.video_list = []

    async def create_session(self) -> None:
        """create client seesion if not exist."""
        if self.session is None:
            conn = aiohttp.connector.TCPConnector(
                force_close=True, enable_cleanup_closed=True, verify_ssl=False
            )
            self.session = aiohttp.ClientSession(headers=self.headers,
                                                 connector=conn,
                                                 trust_env=True)

    async def close_session(self) -> None:
        """close client session if possible."""
        if self.session:
            await self.session.close()

    async def fetch_html(self, url: str) -> tuple:
        """get url's html source code from internet."""
        async with self.session.get(url=url, proxy=self.proxy) as r:
            # maybe exist redirection
            # TODO: watch out more redirections to modify index in r.history
            if r.history:
                url = r.history[0].headers['location']
            return await r.text(), url

    async def fetch_content(self, url: str, params: None) -> str:
        """fetch content from url."""
        async with self.session.get(
            url=url, proxy=self.proxy, params=params
        ) as r:
            return await r.read()

    async def fetch_json(self, url: str) -> dict:
        """fetch json from url."""
        async with self.session.get(url=url, proxy=self.proxy) as r:
            return await r.json()

    async def before_download(self) -> None:
        """do something before download"""
        raise NotImplementedError

    async def downloading(self) -> None:
        """download video from web."""
        tasks = []
        for video in self.video_list:
            video.choose_collection()
            tasks.append(video.download())

        await asyncio.gather(*tasks)

    async def after_downloaded(self) -> None:
        """do something after downloaded video."""
        pass

    async def run(self) -> None:
        """start crawl."""
        info('site', self.site)
        await self.create_session()

        await self.before_download()
        await self.downloading()
        await self.after_downloaded()

        await self.close_session()
