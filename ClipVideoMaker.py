import ffmpeg
from youtube_dl import YoutubeDL
from Types import Clip

def make_clip_video(clip: Clip, video_id: str, dist: str) -> str:
    with YoutubeDL() as ydl:
        info = ydl.extract_info(video_id, download=False)
        video_format = info["requested_formats"][0]
        audio_format = info["requested_formats"][1]

        formats = ydl.cookiejar._cookies[".youtube.com"]["/"].items()
        cookies = "\n".join(
            [f"{cookie[0]}={cookie[1].value}; domain={cookie[1].domain}; path={cookie[1].path}" for cookie in formats]
        )

        (
            ffmpeg
                .concat(
                    ffmpeg.input(video_format["url"], ss=clip.start, t=clip.duration),
                    ffmpeg.input(audio_format["url"], ss=clip.start, t=clip.duration),
                    v=1,
                    a=1
                ).output(
                    dist,
                    vcodec="libx264",
                    bufsize=f"{int(video_format['tbr'])}k",
                    video_bitrate=f"{int(video_format['tbr'])}k",
                    audio_bitrate=f"{int(audio_format['tbr'])}k",
                    crf=18
                ).global_args("-y")
                .global_args("-cookies", cookies)
                .global_args("-reconnect", "1")
                .global_args("-reconnect_streamed", "1")
                .global_args("-reconnect_delay_max", "5")
                .run()
        )

    return dist

def concat_videos(video_paths_txt_path: str, dist: str) -> str:
    (
        ffmpeg
            .input(video_paths_txt_path, f="concat", safe="0")
            .output(dist, c="copy")
            .global_args("-y")
            .run()
    )

    return dist
