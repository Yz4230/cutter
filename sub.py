import os
import json

VIDEO_PATH = "c9VYairGvn4"
DETAILS_PATH = os.path.join(VIDEO_PATH, "details.json")
DESCRIPTION_PATH = os.path.join(VIDEO_PATH, "description.txt")

DESCRIPTION_TEMPLATE = \
"""元動画様はこちら↓
{original_video_title}
{original_video_url}

チャンネルはこちら↓
{uploader_name}
{uploader_url}

この動画は全てAIによって作成されています。"""

with open(DETAILS_PATH, mode="r", encoding="utf-8") as rf:
    details = json.load(rf)

description = DESCRIPTION_TEMPLATE.format(
    original_video_title=details["title"],
    original_video_url=details["webpage_url"],
    uploader_name=details["uploader"],
    uploader_url=details["uploader_url"]
)

with open(DESCRIPTION_PATH, mode="w", encoding="utf-8") as wf:
    wf.write(description)
