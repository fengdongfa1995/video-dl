"""Library for handling video.

Some online video website stores their video (picture) and audio (sound)
separately in differrent place. So, if we want to download a complete video,
we should download video and audio (I say, media) first, and then merge them to
one.

when downloading a single media, if its size exceeds a certain threshold,
program will slice it to many fragments and download with different coroutine.

Available function:
    - Media().download: download a media from internet.
    - MediaCollection().download: download medias contained in MediaCollection.
    - MediaCollection().merge: combined medias contained in collection to one.

Typical usage example:
    media1 = Media(**{'url': 'url1', 'name': '1', size: '1', folder: '.'})
    media2 = Media(**{'url': 'url2', 'name': '2', size: '2', folder: '.'})
    media_collection = MediaCollation([media1, media2])
    for media in media_collection:
        media.download()
"""
from typing import List, Optional
import aiohttp
import asyncio
import contextvars
import math
import os
import subprocess

from prettytable import PrettyTable

from video_dl.toolbox import Config, info, ConsoleColor


session = contextvars.ContextVar('Aiohttp.ClientSession')
semaphore = contextvars.ContextVar('asyncio.Semaphore')


class Media(object):
    """Class used to handle media."""
    _config = Config()

    _chunk_size = _config.chunk_size
    _threshold = _config.big_file_threshold

    def __init__(self, *, url: str, location: str, size: Optional[int] = 0,
                 desc: Optional[str] = 'null'):
        """Initialize a media object.

        Args:
            url: target url.
            size: media's file size. will be used to sort.
            desc: description of media, default: null.
        """
        self.url = url  # download media from this url
        self.location = location  # download to this location
        self.size = size  # file size fetched from server
        self.desc = desc  # description for choosing by user

        self._current_size = 0  # file size during downloading process

    def _get_location(self, index: Optional[int] = 0) -> str:
        """get media slice's target storage path.

        insert a index into file name and return.

        Args:
            index: index of media slice. defalut value is 0 means no slice.

        Returns:
            media slice's target storage location. e.g.: ./media_p_2.mp4.
        """
        if index == 0:
            return self.location
        else:
            folder, name = os.path.split(self.location)
            title, suffix = os.path.splitext(name)
            return os.path.join(folder, f'{title}_p_{index}{suffix}')

    async def _set_size(self) -> None:
        """set media file's real size by parsing server's response headers."""
        headers = {'range': 'bytes=0-1'}
        async with session.get().get(url=self.url, headers=headers) as r:
            self.size = int(r.headers['Content-Range'].split('/')[1])

    def _get_headers(self, index: Optional[int] = 0) -> dict:
        """get a header should be sent to server for downloading a media slice.

        Args:
            index: index of media slice. default value 0 means no slice.

        Returns:
            a request header with slice range. defalut: {}.
        """
        if index == 0:
            return {}

        slice_point = range(0, self.size, self._threshold)
        start_point = slice_point[index - 1]
        end_point = min(start_point + self._threshold - 1, self.size - 1)
        return {'range': f'bytes={start_point}-{end_point}'}

    async def download(self) -> None:
        """download media to target location."""
        info('ready to download', os.path.split(self.location)[1])

        await self._set_size()
        if self.size <= self._threshold:  # don't need silce
            await self._download_slice()
            print()
        else:
            # slice media, create task and run
            slice_count = math.ceil(self.size / self._threshold)
            await asyncio.wait([
                asyncio.create_task(self._download_slice(index + 1))
                for index in range(slice_count)
            ])

            print()
            info('merge', f'merging to {self.location}')
            with open(self.location, 'wb') as f:
                for index in range(slice_count):
                    target = self._get_location(index + 1)
                    with open(target, 'rb') as media_slice:
                        f.write(media_slice.read())
                    os.remove(target)

    async def _download_slice(self, index: Optional[int] = 0) -> None:
        """download media slice from internet

        @param index: index of media slice which we want to download. default
                    value 0 means no slice.
        """
        target = self._get_location(index)  # get target location to save media
        headers = self._get_headers(index)  # get headers to send to server

        async with semaphore.get():
            async with session.get().get(url=self.url, headers=headers) as r:
                with open(target, 'wb') as f:
                    async for chk in r.content.iter_chunked(self._chunk_size):
                        f.write(chk)

                        self._current_size += self._chunk_size
                        self._print_progress()

    def _print_progress(self) -> None:
        """print a naive progress bar."""
        progress = int(self._current_size / self.size * 20)
        print('\r', ConsoleColor.WARNING, '[downloading] ',
              ConsoleColor.OKGREEN,
              f'[{progress*100/20:3.0f}%]',  # percent
              f'({self._current_size/1024/1024:6.2f}/',  # current_siz
              f'{self.size/1024/1024:6.2f}MB)|',  # total_size
              'x' * progress, '.' * (20 - progress),  # naive progress bar
              '\r', ConsoleColor.ENDC, sep='', end='')


class MediaCollection(list):
    """class for handle list of medias."""
    _config = Config()

    def __init__(self, members: List[Media] = None, salt: Optional[str] = ''):
        """Initialization

        Args:
            members: list of Medias.
            salt: a string will be inserted into file name.
        """
        if members is None:
            members = []
        super().__init__(members)

        self.salt = salt
        self.location = None

    def get_location(self) -> str:
        """return media collection's location, add salt."""
        if self.salt == '':
            return self.location
        else:
            folder, name = os.path.split(self.location)
            title, suffix = os.path.splitext(name)
            return os.path.join(folder, f'{title}_{self.salt}{suffix}')

    def add_media(self, url: str, size: int, desc: str) -> None:
        super().append(Media(
            url=url, size=size, desc=desc, location=self.get_location()
        ))

    async def download(self) -> None:
        """download all medias contained in this collection."""
        await asyncio.wait([
            asyncio.create_task(item.download()) for item in self
        ])

    def __str__(self):
        """print this media collection with pretty format."""
        tb = PrettyTable()
        tb.field_names = ['index', 'name', 'desc', 'size']
        for index, media in enumerate(self, 1):
            tb.add_row([index, os.path.split(media.location)[1],
                        media.desc, media.size])
        return tb.get_string()

    def merge(self) -> None:
        """merge all medias into a complete one.

        only workable after all medias are ready.
        """
        info('merge', f'merging to {self.location} ...')

        # command line command
        cmd = ['ffmpeg']
        for item in self:
            cmd += ['-i', item.location]
        cmd += ['-codec', 'copy', self.location, '-y']

        # call command provided by opration system
        subprocess.run(cmd, stdout=subprocess.DEVNULL,
                       stderr=subprocess.STDOUT, check=True)

        # remove temporary files
        for item in self:
            os.remove(item.location)

    # TODO: sort items in MediaCollection,
    # because we download the first item in list by default.
    def todo_sorted(self):
        pass


class Video(object):
    """presents a video."""
    # TODO: combine config file and user's input
    _config = Config()

    def __init__(self, suffix: Optional[str] = 'mp4'):
        """Initialize a video object.

        Args:
            suffix: the suffix of video file. default: mp4.
        """
        self.suffix = suffix

        # attributes read from config file or user's input
        self.root_folder = self._config.download_folder
        self.use_parent_folder = None

        # attributes should be set by spider
        self.parent_folder = None
        self.title = None

        # media collection used to hold url and target location
        self.media_collection = {
            'picture': MediaCollection(salt='picture'),  # video without sound
            'sound': MediaCollection(salt='sound'),  # video without picture
            'video': MediaCollection(salt=''),  # video = picture + sound
        }

    def get_folder(self) -> str:
        """return video's store folder."""
        if self.parent_folder is not None and self.use_parent_folder is True:
            return os.path.join(self.root_folder, self.parent_folder)
        return self.root_folder

    def get_location(self) -> str:
        """return video's store location."""
        return os.path.join(self.get_folder(), f'{self.title}.{self.suffix}')

    def add_media(self, url: str, size: int, desc: Optional[str] = 'null',
                  target: Optional[str] = 'video') -> None:
        """add a media to the specific media collection.

        Args:
            meta_data: basic information of a media resource. should be a dict
                with keys: url, size, desc
            target: the collection will add a media resource. default value is
                'video', means the media with picture and sound.
        """
        self.media_collection[target].location = self.get_location()
        self.media_collection[target].add_media(url, size, desc)

    def choose_collection(self, flag: bool) -> MediaCollection:
        """choose download task from media collection.

        Args:
            flag: Do you want to choose media by yourself?

        Returns:
            download task
        """
        if len(self.media_collection['video']) != 0:
            # choose from 'video' media collection
            raise NotImplementedError('just wait!')
        else:
            # choose from 'picture' and 'sound' media collection
            if flag is False:
                info('choose', 'using default value...')
                self.media_collection['video'] = MediaCollection([
                    self.media_collection['picture'][0],
                    self.media_collection['sound'][0],
                ])
            else:
                info('choose', 'please choose a video below...')
                print(self.media_collection['picture'])
                info('choose', 'please choose a audio below...')
                print(self.media_collection['sound'])

                answer = input("What's your answer(default: 1 1):").strip()
                if not answer:
                    v, a = 1, 1
                else:
                    v, a = [int(item) for item in answer.split(' ')]
                self.media_collection['video'] = MediaCollection([
                    self.media_collection['picture'][v - 1],
                    self.media_collection['sound'][a - 1],
                ])

            # set media collection's location
            self.media_collection['video'].location = self.get_location()
            info('choosed', '↓↓↓↓↓↓↓↓↓↓↓')
            print(self.media_collection['video'])

    async def download(self, client_session: aiohttp.ClientSession) -> None:
        """download medias contained in video media collection."""
        session.set(client_session)
        semaphore.set(asyncio.Semaphore(self._config.max_conn))
        await self.media_collection['video'].download()

    def merge(self) -> None:
        """merge medias contained in video media collection."""
        self.media_collection['video'].merge()
