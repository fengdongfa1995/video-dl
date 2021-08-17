"""Library for Control flow."""
from media import Media, MediaCollection
from toolbox import UserAgent, Config

import argparse
import asyncio
import json
import os
import platform
import re
import time

import aiohttp
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
        self.title = None
        self.file_path = None

        self.session = None
        self.video_list = MediaCollection()
        self.audio_list = MediaCollection()

        # from resolution id to description dictionary
        self.id2desc = None

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
        async with self.session.get(url=target_url) as r:
            resp = await r.text()

        # get video's title and set file path
        state = json.loads(self.re_initial_state.search(resp).group(1))
        self.title = state['videoData']['title']
        self.file_path = os.path.join(
            self.download_folder, f'{self.title}.mp4'
        )

        playinfo = json.loads(self.re_playinfo.search(resp).group(1))

        if self.id2desc is None:
            desc = playinfo['data']['accept_description']
            quality = playinfo['data']['accept_quality']
            self.id2desc = {
                str(key): value for key, value in zip(quality, desc)
            }

        videos = playinfo['data']['dash']['video']
        for video in videos:
            self.video_list.append(Media(**{
                'url': video['base_url'],
                'name': self.title,
                'size': video['bandwidth'],
                'folder': self.download_folder,
                'salt': 'video',
                'desc': (
                    self.id2desc[str(video['id'])] + ' + ' + video['codecs']
                ),
            }))

        audios = playinfo['data']['dash']['audio']
        for audio in audios:
            self.audio_list.append(Media(**{
                'url': audio['base_url'],
                'name': self.title,
                'size': audio['bandwidth'],
                'folder': self.download_folder,
                'salt': 'audio',
            }))

    async def run(self, args) -> None:
        """run!run!run!run!run!run!run!run!run!

        Args:
            args: command line parameters
        """
        await self._create_session()
        await self._parse_html(args.url)

        # determine download task and download
        target_collection = self._choose_collection(args.interactive)
        await target_collection.download(self.session)

        target_collection.merge(self.file_path)

        await self._close_session()

    def _choose_collection(self, flag: bool) -> MediaCollection:
        """choose download task from media collection.

        Args:
            flag: Do you want to choose media by yourself?

        Returns:
            download task
        """
        # choose first media by default
        if not flag:
            return MediaCollection([
                self.video_list[0], self.audio_list[0]
            ])

        print('脚本从目标网站处获取到如下视频信息...')
        print(self.video_list)
        print('\n', '脚本从目标网站处获取到如下音频信息...')
        print(self.audio_list)

        answer = input('请输入欲下载文件序号(默认为：1 1):').strip()
        if not answer:
            v, a = 1, 1
        else:
            v, a = [int(item) for item in answer.split(' ')]

        return MediaCollection([
            self.video_list[v - 1], self.audio_list[a - 1]
        ])


def main():
    parser = argparse.ArgumentParser('python3 bilibili.py')
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
    print(f'视频下载完毕，总计用时 {time.time()-start_time:.2f} 秒！')


if __name__ == '__main__':
    main()
