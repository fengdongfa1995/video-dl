"""Library for Control flow."""
import argparse
import asyncio
import json
import platform
import re
import time

import aiohttp

from video_dl.media import Video
from video_dl.toolbox import UserAgent, Config, info

if platform.system() != 'Windows':
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


class Bilibili(object):
    """Bilibili video downloader."""
    site = 'bilibili'
    home_url = 'https://www.bilibili.com'

    _config = Config()
    download_folder = _config.download_folder

    # come re pattern to extract information from html source code
    re_initial_state = re.compile(r'window.__INITIAL_STATE__=(.*?);')
    re_playinfo = re.compile(r'window.__playinfo__=(.*?)</script>')

    def __init__(self):
        self.session = None
        self.video = Video()

        # from resolution id to description dictionary
        self.id2desc = None

        info('site', self.site)

    async def _create_session(self) -> None:
        if self.session is None:
            headers = {
                'user-agent': UserAgent().random,
                'cookie': self._config.cookie(self.site),
                'referer': self.home_url,
                'origin': self.home_url,
                'accept': '*/*',
            }
            self.session = aiohttp.ClientSession(headers=headers)

    async def _close_session(self) -> None:
        if self.session:
            await self.session.close()

    async def _parse_html(self, target_url: str) -> None:
        """extract key information from html source code.

        Args:
            target_url: target url copied from online vide website.
        """
        info('url', target_url)
        async with self.session.get(url=target_url) as r:
            resp = await r.text()

        # get video's title and set file path
        state = json.loads(self.re_initial_state.search(resp).group(1))
        self.video.title = state['videoData']['title']

        playinfo = json.loads(self.re_playinfo.search(resp).group(1))
        if self.id2desc is None:
            desc = playinfo['data']['accept_description']
            quality = playinfo['data']['accept_quality']
            self.id2desc = {
                str(key): value for key, value in zip(quality, desc)
            }

        videos = playinfo['data']['dash']['video']
        for video in videos:
            self.video.add_media(
                url=video['base_url'],
                size=video['bandwidth'],
                desc=self.id2desc[str(video['id'])] + ' + ' + video['codecs'],
                target='picture',
            )

        audios = playinfo['data']['dash']['audio']
        for audio in audios:
            self.video.add_media(
                url=audio['base_url'],
                size=audio['bandwidth'],
                target='sound',
            )

    async def run(self, args) -> None:
        """run!run!run!run!run!run!run!run!run!

        Args:
            args: command line parameters
        """
        await self._create_session()
        await self._parse_html(args.url)

        # determine download task and download
        self.video.choose_collection(args.interactive)
        await self.video.download(self.session)
        self.video.merge()

        await self._close_session()


def main():
    parser = argparse.ArgumentParser(
        'video_dl',
        description='A naive online video downloader based on aiohttp')
    parser.add_argument(
        '-i', '--interactive', action='store_true',
        help='Manually select download resources.'
    )
    parser.add_argument(
        'url', help='target url copied from online video website.'
    )
    args = parser.parse_args()

    app = Bilibili()
    start_time = time.time()
    asyncio.run(app.run(args))
    print(f'job done! just wasted your time: {time.time()-start_time:.2f}s!')


if __name__ == '__main__':
    main()
