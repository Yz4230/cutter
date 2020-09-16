import json
from youtube_dl import YoutubeDL

def save_video_details(video_id: str, dist: str) -> str:
    with YoutubeDL() as ydl:
        info = ydl.extract_info(video_id, download=False)

    with open(dist, mode='w', encoding='utf-8') as wf:
        json.dump(info, wf, ensure_ascii=False, indent=2)

    return dist
