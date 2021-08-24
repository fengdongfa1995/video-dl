"""Spider for bilibili.com"""
import asyncio
import re

from video_dl.spider import Spider
from video_dl.toolbox import info
from video_dl.video import Video, Media
from video_dl.extractor import Extractor
from video_dl.sites.bilibili.json2ass import Convertor


class BilibiliSpider(Spider):
    """spider for bilibili.com"""
    site = 'bilibili.com'
    home_url = 'https://www.bilibili.com'

    pattern = [
        re.compile('bilibili.com/bangumi/play/ep.*'),
        re.compile('bilibili.com/video/BV.*'),
    ]

    def __init__(self):
        super().__init__()

        self.dm_url = 'https://api.bilibili.com/x/v2/dm/web/seg.so'

        self.list_video_already_flag = False

        self.extractor = None

    async def before_download(self) -> None:
        await self.parse_html(self.url)

    async def after_downloaded(self) -> None:
        for video in self.video_list:
            # download danmaku of each video
            await self.get_dm(video)

            # merge picture and sound to a complete video
            video.merge()

    async def parse_html(self, target_url: str) -> None:
        """extract key information from html source code.

        Args:
            target_url: target url copied from online vide website.
        """
        info('url', target_url)
        resp, target_url = await self.fetch_html(target_url)
        self.extractor = Extractor.create(target_url)

        # should we extract video information in this target_url
        extract_flag = False
        for pattern in self.pattern:
            if pattern.search(target_url):
                extract_flag = True
                break

        if extract_flag is False:
            urls = self.extractor.generate_urls(resp, self.url)
            await self.parse_html(next(urls))
            return

        video = self.create_video()
        video.title = self.extractor.get_title(resp)

        if self.lists:
            video.parent_folder = self.extractor.get_parent_folder(resp)

        try:
            for picture in self.extractor.get_pictures(resp):
                video.add_media(Media(**picture), target='picture')
        except Exception:  # pylint: disable=W0703
            info(
                'failed',
                f'check authority in {target_url} or post it to github issues',
                'https://github.com/fengdongfa1995/video-dl/issues'
            )
            return

        for sound in self.extractor.get_sounds(resp):
            video.add_media(Media(**sound), target='sound')

        # ready to download dabmaku
        oid, pid = self.extractor.get_oid_pid(resp, target_url)
        video.meta_data['oid'] = oid
        video.meta_data['pid'] = pid

        self.video_list.append(video)

        # tring to get a playlist contains this video
        if self.lists and not self.list_video_already_flag:
            info('list', 'tring to fetch more videos...')
            self.list_video_already_flag = True
            tasks = [self.parse_html(url)
                     for url in self.extractor.generate_urls(resp, self.url)]

            if tasks:
                info('list', f'fetched {len(tasks)} more video(s)...')
                await asyncio.gather(*tasks)
            else:
                info('list', 'fetched nothing!')

    async def get_dm(self, video: Video) -> None:
        """fetch video's danmaku."""
        danmaku_list = []
        params = {
            'oid': video.meta_data['oid'],
            'pid': video.meta_data['pid'],
            'type': 1,
        }

        page_index = 1
        while True:
            params.update({'segment_index': page_index})
            page_index += 1

            content = await self.fetch_content(url=self.dm_url, params=params)

            if content:
                danmaku_list += self.extractor.get_dm(content)
            else:
                break

        convertor = Convertor()
        convertor.edit_header(video.title)
        for item in danmaku_list:
            try:
                convertor.json2ass(item)
            except KeyError:
                pass
        video.save_to_disk(convertor.output(), 'ass')
        info('subtitle', 'save to', video.get_folder())
