"""Spider for bilibili.com"""
import asyncio

from video_dl.spider import Spider
from video_dl.toolbox import info
from video_dl.video import Video, Media
from video_dl.extractor import Extractor


class BilibiliSpider(Spider):
    """spider for bilibili.com"""
    site = 'bilibili.com'
    home_url = 'https://www.bilibili.com'

    def __init__(self):
        super().__init__()

        # video definition's id to definition's description
        self.id2desc = None
        self.video_pages = set()
        self.extractor = Extractor.create(self.url)

    async def before_download(self) -> None:
        # parse origin html
        await self.parse_html(self.url)

        if self.lists and self.video_pages:
            info('list', 'tring to fetch more videos...')
            await asyncio.wait([asyncio.create_task(self.parse_html(url))
                                for url in self.video_pages])

        # choose media resource
        for video in self.video_list:
            video.choose_collection()

    def after_downloaded(self) -> None:
        for video in self.video_list:
            video.merge()

    async def parse_html(self, target_url: str) -> None:
        """extract key information from html source code.

        Args:
            target_url: target url copied from online vide website.
        """
        info('url', target_url)
        resp = await self.fetch_html(target_url)

        video = Video(self.session)  # need a session to access internet
        video.title = self.extractor.get_title(resp)
        video.parent_folder = self.extractor.get_parent_folder(resp)

        try:
            for picture in self.extractor.get_pictures(resp):
                video.add_media(Media(**picture), target='picture')
        except KeyError:
            info('fail', f'please check your authority in {target_url}')
            return

        for sound in self.extractor.get_sounds(resp):
            video.add_media(Media(**sound), target='sound')

        if not self.video_pages:
            self.video_pages.update(
                self.extractor.generate_urls(resp, self.url))

        self.video_list.append(video)
