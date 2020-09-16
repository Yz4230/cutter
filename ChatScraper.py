import bs4
import requests
import json
import re
import time
from youtube_dl import YoutubeDL
from concurrent.futures import ThreadPoolExecutor
from collections import deque
from typing import Deque, List, Dict, Tuple, Optional
from logging import getLogger
from datetime import timedelta


class ChatScraper:
    YT_CHAT_API_URL = "https://www.youtube.com/youtubei/v1/live_chat/get_live_chat_replay?continuation={continuation}%253D&key={key}"
    YT_URL_BASE = "http://www.youtube.com/watch?v={video_id}"

    # チャットAPIに送信するデータ
    YT_CHAT_API_DATA = json.dumps({
        "hidden": False,
        "context": {
            "client": {
                "hl": "en",
                "gl": "JP",
                "userAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36,gzip(gfe)",
                "clientName": "WEB",
                "clientVersion": "2.20200822.00.00",
                "osName": "X11",
                "browserName": "Chrome",
                "browserVersion": "84.0.4147.125"}
        }
    })

    # アクセスに使用するヘッダ
    ACCESS_HEADERS = {
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36,gzip(gfe)"
    }

    def __init__(self, video_id: str, show_progress: bool = True):
        self.chat_data: List = []
        self.show_progress = show_progress
        self.video_id = self.parse(video_id)
        self.logger = getLogger(f"{ChatScraper.__name__}({self.video_id})")
        with YoutubeDL() as ydl:
            self.video_details: dict = ydl.extract_info(self.video_id, download=False)

    @staticmethod
    def parse(url: str) -> Optional[str]:
        if re_result := re.search(r"[A-Za-z0-9_-]{11}", url):
            return re_result.group()
        return None

    # チャットAPIからチャットを取得する関数
    @classmethod
    def __fetch_chat_api(cls, sess: requests.Session, continuation: str, api_key: str) -> dict:
        api_url = cls.YT_CHAT_API_URL.format(
            continuation=continuation, key=api_key)
        res = sess.post(api_url, cls.YT_CHAT_API_DATA, headers=cls.ACCESS_HEADERS.update(
            {"content-type": "application/json"}))
        return res.json()

    # def __process_message_data(self, data: dict) -> Optional[dict]:
    #     try: 
    #         result = {}
    #         action: dict = data["actions"][0]["addChatItemAction"]["item"]["liveChatTextMessageRenderer"]
    #         runs: List[dict] = action["message"]
    #         message = ""
    #         for run in runs:
    #             message += run.get("text", "")
    #         result["message"] = message
    #         result["authorName"] = action["authorName"]["simpleText"]
    #         result["timestampUsec"] = int(action["timestampUsec"])
    #         result["offsetMsec"] = int(data["videoOffsetTimeMsec"])
    #         return data
    #     except:
    #         return None

    # チャットデータ処理
    def __handle_message_data(self, args: Tuple[int, List[Dict], Deque]) -> None:
        index, data, dq = args
        if index == 1:
            data = data[1:]
        fetched_chat_data = deque()
        for action in data:
            try:
                fetched_chat_data.append(action["replayChatItemAction"])
            except KeyError:
                continue
        dq.append((index, fetched_chat_data))

    def run(self) -> List:
        chat_data = deque()

        with requests.Session() as session, ThreadPoolExecutor(max_workers=4) as executor:
            self.logger.info(f"Start scraping...")
            start_time = time.time()

            html = session.get(self.YT_URL_BASE.format(
                video_id=self.video_id), headers=self.ACCESS_HEADERS)
            soup = bs4.BeautifulSoup(html.text, "html.parser")

            # データの取得に使うAPIキー
            api_key = re.search(
                r'"INNERTUBE_API_KEY":"(.*?)"', soup.text).group(1)
            # 取得するための最初のトークン
            first_chat_continuation = re.search(
                r'"continuation":"([a-zA-Z0-9]+)"', soup.text).group(1)
            # 取得した最初のチャットデータ
            fetched_data = self.__fetch_chat_api(
                session, first_chat_continuation, api_key)
            # チャットAPIにアクセスした回数
            access_count = 1
            #動画の秒数
            video_duration: int = self.video_details["duration"]

            while(True):
                try:
                    continuation_data = fetched_data["continuationContents"]["liveChatContinuation"]
                    next_continuation = continuation_data["continuations"][0]["liveChatReplayContinuationData"]["continuation"].rstrip("%3D")
                    actions = continuation_data["actions"]

                    executor.submit(self.__handle_message_data,
                                    (access_count, actions, chat_data))
                    if self.show_progress:
                        last_chat_time = int(actions[-1]["replayChatItemAction"]["videoOffsetTimeMsec"]) // 1000
                        ratio = last_chat_time / video_duration
                        progress_bar = int(ratio * 32)
                        print(f"\r[{'*' * progress_bar}{'_' * (32 - progress_bar)}] {ratio * 100:.2f}% "
                            f"last comment time: {timedelta(seconds=last_chat_time)}", end="")

                    fetched_data = self.__fetch_chat_api(
                        session, next_continuation, api_key)
                    access_count += 1
                except KeyError:
                    if self.show_progress:
                        print("")
                    break

        chat_data = list(chat_data)
        chat_data = sum(map(lambda i: list(i[1]), sorted(
            chat_data, key=lambda i: i[0])), [])
        self.chat_data = list(chat_data)
        self.logger.info(
            f"Finished scraping in {time.time() - start_time:.1f} seconds.")

        return self.chat_data

    def save(self, dist: Optional[str] = None) -> str:
        self.logger.info("Saving chat data...")
        start_time = time.time()
        escaped_title = re.sub(r"\\|\/|<|>|\||:|&", "", self.video_details["title"])
        _filename = dist or f"chats--{self.video_id}--{escaped_title}.json"
        with open(_filename, mode="w", encoding="utf-8") as wf:
            json.dump(self.chat_data, wf, ensure_ascii=False, indent=2)
        self.logger.info(
            f"The chat data was saved as '{dist}' in {time.time() - start_time:.1f} seconds successfully.")

        return _filename