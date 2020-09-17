import os

from concurrent.futures import ProcessPoolExecutor
from ChatScraper import ChatScraper
from HotExplorer import HotExplorer
from ClipVideoMaker import make_clip_video, concat_videos
from Tools import save_video_details

user_input = input("URL here : ")
video_id = ChatScraper.parse(user_input)

dist = f"./{video_id}"
os.makedirs(dist, exist_ok=True)

video_details_path = save_video_details(
    video_id, os.path.join(dist, "details.json"))
print(f"The details of '{video_id}' was saved at {video_details_path}")

scraper = ChatScraper(video_id, show_progress=True)
chat_data = scraper.run()
scraper.save(os.path.join(dist, "chats.json"))

explorer = HotExplorer(chat_data)
clips = explorer.explore()


def wrap_make_clip_video(args):
    return make_clip_video(*args)


with ProcessPoolExecutor(max_workers=2) as executor:
    executor.map(
        wrap_make_clip_video,
        [(clip, video_id, os.path.join(dist, f"{clip.start}-{clip.end}.mp4"), True) for clip in clips]
    )

clipvideo_filenames = [f"{clip.start}-{clip.end}.mp4" for clip in clips]
videos_text_path = os.path.join(dist, "videos.txt")
with open(videos_text_path, mode="w", encoding="utf-8") as wf:
    wf.write("\n".join([f"file {fname}" for fname in clipvideo_filenames]))

hotclips_path = concat_videos(
    videos_text_path, os.path.join(dist, "hotclips.mp4"))
print(f"Hotclips video was saved at {hotclips_path}")
