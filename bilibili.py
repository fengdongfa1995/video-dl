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

from media import Media, MediaCollection
from toolbox import USERAGENT, CONFIG


class Bilibili(object):
    """B站视频下载器"""
    site = 'bilibili'
    home_url = 'https://www.bilibili.com'

    # 视频存储路径
    download_folder = CONFIG.download_folder

    # 抽取关键信息的正则表达式
    re_initial_state = re.compile(r'window.__INITIAL_STATE__=(.*?);')
    re_playinfo = re.compile(r'window.__playinfo__=(.*?)</script>')

    def __init__(self):
        # 音视频资源列表
        self.video_list = MediaCollection()
        self.audio_list = MediaCollection()

        # 会话管理器
        self.session = None

        # 清晰度的id与描述对应字典
        self.id2desc = None

        # 视频标题
        self.title = None

        # 视频存储路径
        self.file_path = None

    async def _create_session(self) -> None:
        """创建会话管理器"""
        if self.session is None:
            headers = {
                'user-agent': USERAGENT.random,
                'cookie': CONFIG.cookie(self.site),
                'referer': self.home_url,
                'origin': self.home_url,
                'accept': '*/*',
            }
            self.session = aiohttp.ClientSession(headers=headers)

    async def _close_session(self) -> None:
        """管理会话管理器"""
        if self.session:
            await self.session.close()

    async def _parse_html(self, target_url: str) -> tuple:
        """解析网页，抽取关键信息

        @param target_url: 目标网址

        @return: 返回获取到的关键信息列表
        """
        # 获取网页源代码
        async with self.session.get(url=target_url) as r:
            resp = await r.text()

        # 获取视频标题
        state = json.loads(self.re_initial_state.search(resp).group(1))
        self.title = state['videoData']['title']

        # 标题和存储路径一同决定视频的存储位置
        self.file_path = os.path.join(
            self.download_folder, f'{self.title}.mp4'
        )

        # 获取音视频网络资源相关信息
        playinfo = json.loads(self.re_playinfo.search(resp).group(1))

        # 设置清晰度ID对应表
        if self.id2desc is None:
            desc = playinfo['data']['accept_description']
            quality = playinfo['data']['accept_quality']
            self.id2desc = {
                str(key): value for key, value in zip(quality, desc)
            }

        # 获取所有可用视频资源
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

        # 获取所有可用音频资源
        audios = playinfo['data']['dash']['audio']
        for audio in audios:
            self.audio_list.append(Media(**{
                'url': audio['base_url'],
                'name': self.title,
                'size': audio['bandwidth'],
                'folder': self.download_folder,
                'salt': 'audio',
            }))

        return (self.video_list, self.audio_list)

    async def run(self, args) -> None:
        """启动爬虫，完成下载任务

        @param args: 命令行参数解析结果
        """
        # 创建会话管理器
        await self._create_session()

        # 解析网页源代码
        await self._parse_html(args.url)

        # 确定下载目标
        target_collection = self._choose_collection(args.interactive)

        # 启动下载任务
        await target_collection.download(self.session)

        # 下载完成后合并音视频文件到目标路径
        target_collection.merge(self.file_path)

        # 关闭会话管理器
        await self._close_session()

    def _choose_collection(self, flag: bool) -> MediaCollection:
        """从现有音视频资源中选择待下载目标

        @param flag: 是否需要手工选择下载目标

        @return: 被选中的下载目标
        """
        # 不用手工选择下载目标时，默认取第一个
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
    # 命令行参数解析器
    parser = argparse.ArgumentParser('python3 bilibili.py')
    parser.add_argument(
        '-i', '--interactive', action='store_true',
        help='Manually select download resources'
    )
    parser.add_argument(
        'url', help='target url copied from online video website'
    )
    args = parser.parse_args()

    app = Bilibili()
    start_time = time.time()
    asyncio.run(app.run(args))
    print(f'视频下载完毕，总计用时 {time.time()-start_time:.2f} 秒！')


if __name__ == '__main__':
    main()
