import requests
import re
import json
from pprint import pprint
import subprocess

target_url = 'https://www.bilibili.com/video/BV1qb4y1z7ve'
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.67',
    'cookie': r"cookie: rpdid=|(YYlkJJ)lk0J'ulmu~)kulJ; blackside_state=1; CURRENT_FNVAL=80; buvid3=8B22432C-3E2E-457A-8472-08039CFA0E5A185014infoc; buvid_fp=8B22432C-3E2E-457A-8472-08039CFA0E5A185014infoc; _uuid=40432882-7878-B51B-AC3F-4ED62C2B2AFF43667infoc; CURRENT_QUALITY=80; CURRENT_BLACKGAP=1; bp_t_offset_40240481=499027250781108389; fingerprint=294a22df52049250f728f7c2797ea1ff; SESSDATA=6a472e2e%2C1644209871%2Cbe8c9%2A81; bili_jct=e233d20b74aff02c748d061ea1d30abc; DedeUserID=40240481; DedeUserID__ckMd5=e9f44d11c9044f2a; sid=6y2ep749; LIVE_BUVID=AUTO5216286779969031; fingerprint3=4dc3cea7f16efd474480e5b7ce9ca1a2; fingerprint_s=87da5cdc522dfc0b5cfc41ba6a2fc4ef; buvid_fp_plain=8B22432C-3E2E-457A-8472-08039CFA0E5A185014infoc; bp_video_offset_40240481=499027250781108389; PVID=1",
    'referer': target_url,
}

resp = requests.get(url=target_url, headers=headers).text
state = re.search(r'window.__INITIAL_STATE__=(.*?);', resp).group(1)
state = json.loads(state)
title = state['videoData']['title']

playinfo = re.search(r'window.__playinfo__=(.*?)</script>', resp).group(1)
playinfo = json.loads(playinfo)

audios = playinfo['data']['dash']['audio']
audio_list = []
for index, audio in enumerate(audios, 1):
    audio_list.append({
        'index': index,
        'url': audio['base_url'],
        'size': audio['bandwidth'],
    })

desc = playinfo['data']['accept_description']
quality = playinfo['data']['accept_quality']
id2desc = {
    str(key): value
    for key, value in zip(quality, desc)
}

videos = playinfo['data']['dash']['video']
video_list = []
for index, video in enumerate(videos, 1):
    video_list.append({
        'index': index,
        'url': video['base_url'],
        'size': video['bandwidth'],
        'codecs': video['codecs'],
        'resolution': f'{video["width"]}x{video["height"]}',
        'desc': id2desc[str(video['id'])],
    })

print('脚本从B站获取到如下音视频信息...')
pprint(video_list)
print()
pprint(audio_list)

answer = input('请输入您要下载的音视频文件序号（视频在前，音频在后，空格隔开）：')
if not answer.strip():
    v_index, a_index = 1, 1
else:
    v_index, a_index = [int(item) for item in answer.strip().split(' ')]

# 正式下载音视频文件
print('正在下载视频文件')
v_url = video_list[v_index - 1]['url']
content = requests.get(url=v_url, headers=headers, stream=True)
with open('video.mp4', 'wb') as f:
    for chunk in content.iter_content(1024):
        if chunk:
            f.write(chunk)

print('正在下载音频文件')
a_url = audio_list[a_index - 1]['url']
content = requests.get(url=a_url, headers=headers, stream=True)
with open('audio.mp4', 'wb') as f:
    for chunk in content.iter_content(1024):
        if chunk:
            f.write(chunk)

# 合并音视频文件
cmd = 'ffmpeg -i video.mp4 -i audio.mp4 -codec copy'
subprocess.run(cmd.split(' ') + [f'{title}.mp4', '-y'])
