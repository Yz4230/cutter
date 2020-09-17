import json
import numpy as np
from Types import Clip
from typing import Union, List
from datetime import timedelta


class HotExplorer:
    YT_URL_BASE = "http://www.youtube.com/watch?v={video_id}&t={time}s"

    def __init__(self, data: Union[str, list], mean_range=10, clip_range=20, max_clips=20):
        self.__data: Union[str, list] = data
        self.__mean_range: int = mean_range
        self.__clip_range: int = clip_range
        self.__max_clips: int = max_clips
        self.__hot_clips: list[Clip] = []

    @staticmethod
    def __is_text_chat(chat: dict) -> bool:
        try:
            timestamp: str = \
                chat["actions"][0]["addChatItemAction"]["item"]["liveChatTextMessageRenderer"]["timestampText"][
                    "simpleText"]
            return "," not in timestamp
        except KeyError:
            return False

    @staticmethod
    def __timestamp_text_to_sec(text: str) -> int:
        elements = list(map(int, text.split(":")))
        if len(elements) == 2:
            return (abs(elements[0]) * 60 + elements[1]) * (-1 if text[0] == "-" else 1)
        else:
            return elements[0] * 3600 + elements[1] * 60 + elements[2]

    @staticmethod
    def __sec_to_str(sec: int) -> str:
        return str(timedelta(seconds=sec))

    @classmethod
    def __make_data(cls, chat: dict) -> dict:
        renderer: dict = chat["actions"][0]["addChatItemAction"]["item"]["liveChatTextMessageRenderer"]
        return {
            "message": "".join([run.get("text", "") for run in renderer["message"]["runs"]]),
            "time": cls.__timestamp_text_to_sec(renderer["timestampText"]["simpleText"]),
            "time_str": renderer["timestampText"]["simpleText"]
        }

    def explore(self):
        if isinstance(self.__data, str):
            with open(self.__data, mode="r", encoding="utf-8") as rf:
                raw_chat_data: list = json.load(rf)
        else:
            raw_chat_data = self.__data

        chat_data = filter(self.__is_text_chat, raw_chat_data)
        chat_data = map(self.__make_data, chat_data)
        chat_data = list(filter(lambda i: i["time"] >= 0, chat_data))

        hist, bins = np.histogram(list(map(lambda i: i["time"], chat_data)),
                                  bins=np.arange(0, chat_data[-1]["time"] + 1))

        mean_range = self.__mean_range
        convolved = np.convolve(hist, np.ones(mean_range) / mean_range, mode="same")

        max_clips = self.__max_clips
        hot_points = convolved.argsort()[:-(max_clips + 1):-1]

        min_time = bins[0]
        max_time = bins[-1]
        clip_range = self.__clip_range
        clips = []
        for point in hot_points:
            for index, clip in enumerate(clips):
                start, end = clip
                if start <= point <= end:
                    clips[index] = [min(start, point - clip_range), max(end, point + clip_range)]
                    break
            else:
                clips.append([point - clip_range, point + clip_range])
        for index, clip in enumerate(clips):
            clips[index] = [int(max(min_time, clip[0])), int(min(max_time, clip[1]))]

        self.__hot_clips += [Clip(clip[0], clip[1]) for clip in clips]

        return self.__hot_clips

    def generate_links(self, video_id: str) -> List[str]:
        return [self.YT_URL_BASE.format(video_id=video_id, time=clip.start) for clip in self.__hot_clips]
