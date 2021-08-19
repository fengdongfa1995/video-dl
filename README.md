# video_dl

`video_dl` is a naive online video downloader based on [aiohttp](https://docs.aiohttp.org/en/stable/).

## Prerequisites
- [ffmpeg](https://ffmpeg.org/).
- [python](https://www.python.org) 3.7 or above (required by [aiohttp](https://docs.aiohttp.org/en/stable/)).

## Installation
```bash
pip3 install video_dl
```

## Upgrading
```bash
pip3 install --upgrade video_dl
```

## Usage
### download the highest-definition video
> :warning: If there are special symbols in your url, please enclose it with quotation marks. 
```bash
video_dl 'https://www.bilibili.com/video/BV15L411p7M8'
```
> :warning: the `highest` depends my own view, maybe not the one you want.

![Normal Usage](https://github.com/fengdongfa1995/video_dl/raw/main/screenshots/normal_usage.gif)
### download video which definition will be selected manually
```bash
video_dl -i 'https://www.bilibili.com/video/BV15L411p7M8'
```
![Normal Usage](https://github.com/fengdongfa1995/video_dl/raw/main/screenshots/interactive.gif)

## Help document
```bash
video_dl -h
```

# Supported websites
- [哔哩哔哩 (゜-゜)つロ 干杯~](https://www.bilibili.com/)

# How this shit was created?
- [在B站学习用Python做一个B站爬虫](https://www.bilibili.com/video/BV1nv411T798/)
