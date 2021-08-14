from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import subprocess

from prettytable import PrettyTable
import requests

from toolbox import CONFIG


class Media(object):
    """音视频资源类"""
    chunk_size = CONFIG.chunk_size

    def __init__(self, url: str, name: str, size: float, desc: str = 'null'):
        """初始化音视频资源对象

        @param url: 在线访问网址
        @param file_name: 存储时文件名
        @param size: 文件大小
        @param description: 描述文本
        """
        self.url = url
        self.name = name
        self.size = size
        self.desc = desc

        # 目标存储路径
        self.target = None

    def download(self, session: requests.Session, folder: str) -> None:
        """下载音视频资源到存储路径

        @param session: 用以访问互联网的会话管理器
        @param folder: 存储路径
        """
        # 确定存储位置
        self.target = os.path.join(folder, self.name)
        print(f'正在将 {self.name} 下载到 {self.target} ...')

        # 启动下载
        content = session.get(url=self.url, stream=True)
        with open(self.target, 'wb') as f:
            for chunk in content.iter_content(self.chunk_size):
                if chunk:
                    f.write(chunk)


class MediaCollection(list):
    """音视频资源列表类"""
    def __init__(self, members: list = []):
        super().__init__(members)

    def download(self, session: requests.Session, folder: str):
        """下载资源列表当中的所有资源"""
        self.folder = folder
        with ThreadPoolExecutor() as pool:
            futures = [
                pool.submit(item.download, session, folder) for item in self
            ]
            list(as_completed(futures))

    def __str__(self):
        """用更加漂亮的方式打印资源列表"""
        tb = PrettyTable()
        tb.field_names = ['index', 'name', 'desc', 'size', 'url']
        for index, media in enumerate(self, 1):
            info = [index, media.name, media.desc, media.size, media.url[:40]]
            tb.add_row(info)

        return tb.get_string()

    def merge(self, target: str) -> None:
        """将资源列表当中所有资源合并成一个视频

        @param target: 视频存储路径
        """
        print(f'正在将资源列表当中的内容合并到 {target} ...')
        cmd = ['ffmpeg']
        for item in self:
            cmd += ['-i', item.target]
        cmd += ['-codec', 'copy', target, '-y']
        subprocess.run(cmd)

        for item in self:
            os.remove(item.target)
