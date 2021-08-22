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
    media1 = Media(**{'url': 'url1', size: '1', desc: '.'})
    media2 = Media(**{'url': 'url2', size: '2', desc: '.'})
    media_collection = MediaCollation([media1, media2])
    media_collection.download()
    media_collection.merge()  # if necessary
"""
from typing import List, Optional
import aiohttp
import asyncio
import contextvars
import math
import os
import subprocess

from prettytable import PrettyTable

from video_dl.args import Arguments
from video_dl.toolbox import ConsoleColor, info, ask_user


session = contextvars.ContextVar('Aiohttp.ClientSession', default=None)
semaphore = contextvars.ContextVar('asyncio.Semaphore', default=None)


class Media(object):
    """Class used to handle media."""
    args = Arguments()

    _threshold = args.big_file_threshold
    _proxy = args.proxy

    def __init__(self, *, url: str,
                 size: Optional[int] = 0,
                 desc: Optional[str] = 'null'):
        """Initialize a media object.

        Args:
            url: target url.
            size: media's file size. will be used to sort.
            desc: description of media, default: null.
        """
        self.url = url  # download media from this url
        self.size = size  # file size fetched from server, will be used to sort
        self.desc = desc  # description for choosing by user

        # download to this location, will be changed by MediaCollection outside
        self.location = None

        # file size during downloading, will be used to draw a progress bar.
        self._current_size = 0

    def _get_location(self, index: Optional[int] = 0) -> str:
        """get media slice's target storage path.

        insert a index into file's name and return.

        Args:
            index: index of media slice. defalut value is 0 means no slice.

        Returns:
            media slice's target storage location. e.g.: ./media_p2.mp4.
        """
        if index == 0:
            return self.location
        else:
            folder, name = os.path.split(self.location)
            title, suffix = os.path.splitext(name)
            return os.path.join(folder, f'{title}_p{index}{suffix}')

    async def _set_size(self) -> None:
        """set media file's real size by parsing server's response headers."""
        headers = {'range': 'bytes=0-1'}
        async with session.get().get(
            url=self.url, headers=headers, proxy=self._proxy
        ) as r:
            self.size = int(r.headers['Content-Range'].split('/')[1])

    def _get_headers(self, index: Optional[int] = 0) -> dict:
        """get a headers should be sent to server for downloading a media slice

        Args:
            index: index of media slice. begin with 1.
                default value 0 means no slice.

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
            print()  # avoid overwritten
        else:
            # slice media, create task and run
            slice_count = math.ceil(self.size / self._threshold)
            await asyncio.wait([
                asyncio.create_task(self._download_slice(index + 1))
                for index in range(slice_count)
            ])

            print()  # avoid overwritten
            info('slices2one', f'merging to {os.path.split(self.location)[1]}')
            with open(self.location, 'wb') as f:
                for index in range(slice_count):
                    target = self._get_location(index + 1)
                    with open(target, 'rb') as media_slice:
                        f.write(media_slice.read())
                    os.remove(target)

    async def _download_slice(self, index: Optional[int] = 0) -> None:
        """download media slice from internet.

        @param index: index of media slice which we want to download.
                    default value 0 means no slice.
        """
        target = self._get_location(index)  # get target location to save media
        headers = self._get_headers(index)  # get headers to send to server

        async with semaphore.get():
            async with session.get().get(
                url=self.url, headers=headers, proxy=self._proxy
            ) as r:
                with open(target, 'wb') as f:
                    async for chunk in r.content.iter_any():
                        f.write(chunk)

                        self._current_size += len(chunk)
                        self._print_progress()

    def _print_progress(self) -> None:
        """print a naive progress bar."""
        progress = int(self._current_size / self.size * 20)
        print('\r', ConsoleColor.WARNING, '[downloading] ',
              ConsoleColor.OKGREEN,
              f'[{progress*100/20:3.0f}%]',  # percent
              f'({self._current_size/1024/1024:6.2f}/',  # current_size
              f'{self.size/1024/1024:6.2f}MB)|',  # total_size
              'x' * progress, '.' * (20 - progress),  # naive progress bar
              ' ', ConsoleColor.OKCYAN, os.path.split(self.location)[1],
              ConsoleColor.ENDC, '\r', ConsoleColor.ENDC, sep='', end='')


class MediaCollection(list):
    """class for handle list of medias."""
    arg = Arguments()

    def __init__(self, members: List[Media] = None, *,
                 salt: Optional[str] = ''):
        """Initialization

        Args:
            members: list of Medias.
            salt: a string will be inserted into file name.
        """
        if members is None:
            members = []
        super().__init__(members)

        self.salt = salt
        self.location = None  # will be set by Video outsite.

    def get_location(self) -> str:
        """return media collection's location, add salt."""
        if self.salt == '':
            return self.location
        else:
            folder, name = os.path.split(self.location)
            title, suffix = os.path.splitext(name)
            return os.path.join(folder, f'{title}_{self.salt}{suffix}')

    def add_media(self, media: Media) -> None:
        """add media resource into media collection."""
        if media.location is None:
            media.location = self.get_location()
        super().append(media)

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
            tb.add_row([
                index, os.path.split(media.location)[1], media.desc, media.size
            ])
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
        subprocess.run(cmd,
                       stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
                       check=True)

        # remove temporary files
        for item in self:
            os.remove(item.location)

    def sort_media(self, reverse: bool = True) -> None:
        """sort medias in media collection, biggest one will be the first."""
        super().sort(key=lambda item: item.size, reverse=reverse)


class Video(object):
    """presents a video."""
    arg = Arguments()

    directory = arg.directory
    interactive = arg.interactive
    lists = arg.lists
    max_conn = arg.max_conn

    def __init__(self, client_session: aiohttp.ClientSession,
                 suffix: Optional[str] = 'mp4'):
        """Initialize a video object.

        Args:
            client_session: session used to access web.
            suffix: the suffix of video file. default: mp4.
        """
        if session.get() is None:
            session.set(client_session)

        if semaphore.get() is None:
            semaphore.set(asyncio.Semaphore(self.max_conn))

        # attributes read from config file or user's input
        self.root_folder = self.directory
        self.use_parent_folder = self.lists

        # attributes should be set by spider
        self.suffix = suffix
        self.parent_folder = None
        self.title = None

        # media collection used to hold url and target location
        self.media_collection = {
            'picture': MediaCollection(salt='picture'),  # video without sound
            'sound': MediaCollection(salt='sound'),  # video without picture
            'video': MediaCollection(),  # video = picture + sound
        }

        # used to hold something else
        self.meta_data = {}

    def get_folder(self) -> str:
        """return video's store folder."""
        if self.parent_folder is not None and self.use_parent_folder is True:
            return os.path.join(self.root_folder, self.parent_folder)
        return self.root_folder

    def get_location(self) -> str:
        """return video's store location."""
        return os.path.join(self.get_folder(), f'{self.title}.{self.suffix}')

    def add_media(self, media: Media, target: Optional[str] = 'video') -> None:
        """add a media to the specific media collection.

        Args:
            media: a Media object represents some information about media.
            target: the collection will add a media resource. default value is
                'video', means the media with picture and sound.
        """
        if self.media_collection[target].location is None:
            self.media_collection[target].location = self.get_location()
        self.media_collection[target].add_media(media)

    def choose_collection(self) -> MediaCollection:
        """choose download task from media collection.

        Args:
            flag: Do you want to choose media by yourself?

        Returns:
            download task
        """
        if len(self.media_collection['video']) != 0:
            self.media_collection['video'].sort_media()

            # choose from 'video' media collection
            if self.interactive is False:
                info('choose', 'using default value (the first one)...')
                v = 1
            else:
                info('choose', 'please choose a video below...')
                print(self.media_collection['video'])
                v = ask_user(count=1, default=1)

            media = self.media_collection['video'][v - 1]
            self.media_collection['video'].clear()
            self.add_media(media)
        else:
            # sort item in media collection
            self.media_collection['picture'].sort_media()
            self.media_collection['sound'].sort_media()

            # choose from 'picture' and 'sound' media collection
            if self.interactive is False:
                info('choose', 'using default value (the first one)...')
                v, a = 1, 1
            else:
                for key in ['picture', 'sound']:
                    info('choose', f'please choose a {key} below...')
                    print(self.media_collection[key])
                v, a = ask_user(count=2, default=1)

            self.add_media(self.media_collection['picture'][v - 1])
            self.add_media(self.media_collection['sound'][a - 1])

        info('choosed', '↓↓↓↓↓↓↓↓↓↓↓')
        print(self.media_collection['video'])

        # save memory
        del self.media_collection['picture']
        del self.media_collection['sound']

    async def download(self) -> None:
        """download medias contained in video media collection."""
        # create directory if necessary
        folder = self.get_folder()
        if folder != self.root_folder:
            if os.path.exists(folder) is False or os.path.isfile(folder):
                os.mkdir(self.get_folder())

        await self.media_collection['video'].download()

    def merge(self) -> None:
        """merge medias contained in video media collection."""
        self.media_collection['video'].merge()

    def save_to_disk(self, content: str, suffix: str) -> None:
        """save something to disk with same name but different suffix."""
        path, _ = os.path.splitext(self.get_location())
        path = f'{path}.{suffix}'
        with open(path, 'w') as f:
            f.write(content)
