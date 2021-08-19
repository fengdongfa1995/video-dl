"""Everything used for downloading video in bilibili.com."""
from urllib.parse import urljoin
import asyncio
import json
import re

from video_dl.spider import Spider
from video_dl.toolbox import info
from video_dl.video import Video, Media


class BilibiliSpider(Spider):
    """spider for bilibili.com"""
    site = 'bilibili.com'
    home_url = 'https://www.bilibili.com'

    # re patterns to extract information from html source code
    re_initial_state = re.compile(r'window.__INITIAL_STATE__=(.*?);')
    re_playinfo = re.compile(r'window.__playinfo__=(.*?)</script>')

    def __init__(self):
        super().__init__()

        # video definition's id to definition's description
        self.id2desc = None
        self.video_pages = set()

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

        video = Video(self.session)  # need a session to access internet

        resp = await self.fetch_html(target_url)

        state = json.loads(self.re_initial_state.search(resp).group(1))
        current_page = state['p']
        pages = state['videoData']['pages']
        for page in pages:
            if page['page'] == current_page:
                video.title = page['part']
            else:
                # if there is other video in the same playlist
                video.parent_folder = state['videoData']['title']  # set folder
                if len(pages) > len(self.video_pages) + 1:
                    self.video_pages.add(  # ready to create task
                        urljoin(self.url, f'?p={page["page"]}')
                    )

        playinfo = json.loads(self.re_playinfo.search(resp).group(1))
        if self.id2desc is None:
            desc = playinfo['data']['accept_description']
            quality = playinfo['data']['accept_quality']
            self.id2desc = {
                str(key): value for key, value in zip(quality, desc)
            }

        videos = playinfo['data']['dash']['video']
        for media in videos:
            video.add_media(Media(
                url=media['base_url'],
                size=media['bandwidth'],
                desc=self.id2desc[str(media['id'])] + ' + ' + media['codecs'],
            ), target='picture')

        audios = playinfo['data']['dash']['audio']
        for media in audios:
            video.add_media(Media(
                url=media['base_url'],
                size=media['bandwidth']), target='sound')

        self.video_list.append(video)
