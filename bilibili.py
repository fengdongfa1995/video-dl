import json
import os
import re

import requests

from media import Media, MediaCollection
from toolbox import USERAGENT, CONFIG


class Bilibili(object):
    """B站视频下载器"""
    site = 'bilibili'
    home_url = 'https://www.bilibili.com'

    # 视频存储路径
    download_folder = CONFIG.download_folder

    # 抽取关键信息用的正则表达式
    re_initial_state = re.compile(r'window.__INITIAL_STATE__=(.*?);')
    re_playinfo = re.compile(r'window.__playinfo__=(.*?)</script>')

    def __init__(self):
        # 新建并配置会话管理器
        self.session = requests.Session()
        self.session.headers.update({
            'user-agent': USERAGENT.random,
            'cookie': CONFIG.cookie(self.site),
            'referer': self.home_url,
        })

        self.video_list = MediaCollection()
        self.audio_list = MediaCollection()

        # 清晰度的id与描述对应字典
        self.id2desc = None

        # 视频标题
        self.title = None
        # 视频存储路径
        self.file_path = None

    def _parse_html(self, target_url: str):
        """解析网页，抽取关键信息

        @param target_url: 目标网址
        """
        # 获取网页源代码
        resp = self.session.get(url=target_url).text

        # 获取视频标题
        state = json.loads(self.re_initial_state.search(resp).group(1))
        self.title = state['videoData']['title']
        self.file_path = os.path.join(self.download_folder,
                                      f'{self.title}.mp4')

        # 获取音视频资源相关信息
        playinfo = json.loads(self.re_playinfo.search(resp).group(1))

        # 获取id与清晰度对应表
        if self.id2desc is None:
            desc = playinfo['data']['accept_description']
            quality = playinfo['data']['accept_quality']
            self.id2desc = {
                str(key): value for key, value in zip(quality, desc)
            }

        # 抽取所有可用音频资源
        audios = playinfo['data']['dash']['audio']
        for audio in audios:
            self.audio_list.append(Media(
                url=audio['base_url'],
                name=f'{self.title}_audio.mp4',
                size=audio['bandwidth']
            ))

        # 抽取所有可用视频资源
        videos = playinfo['data']['dash']['video']
        for video in videos:
            self.video_list.append(Media(
                url=video['base_url'],
                name=f'{self.title}_video.mp4',
                size=video['bandwidth'],
                desc=self.id2desc[str(video['id'])] + ' + ' + video['codecs']
            ))

    def download(self, target_url: str):
        """提供给用户的API，下载视频

        @param target_url: 目标网址
        """
        # 解析网页源代码
        self._parse_html(target_url)

        print('脚本从B站获取到如下音视频信息...')
        print('请在这里找准您想要下载的视频信息！')
        print(self.video_list)
        print('\n请在这里找准您想要下载的音频信息！')
        print(self.audio_list)

        answer = input('请输入欲下载文件的序号（默认取第一个）：').strip()
        if not answer:
            v_index, a_index = 1, 1
        else:
            v_index, a_index = [int(item) for item in answer.split(' ')]

        # 抽取出下载链接
        target_collection = MediaCollection([self.video_list[v_index - 1],
                                             self.audio_list[a_index - 1]])
        print('\n您选中的音视频资源：\n', target_collection)

        target_collection.download(self.session, self.download_folder)
        target_collection.merge(self.file_path)


def main():
    import sys
    url = sys.argv[1]

    app = Bilibili()
    app.download(url)
    print('job done!')


if __name__ == '__main__':
    main()
