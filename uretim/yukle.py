"""Boncuk Otomasyon: complete upload script (YouTube Data API v3, videos.insert).

Uploads one of the channel owner's own videos to the owner's own channel, marked
"made for kids", and schedules it with status.publishAt. The daily job
(uretim/gunluk.py) calls the same youtube_api.video_yukle() function.

Usage:
  python uretim/yukle.py VIDEO.mp4 --title "Title" --description-file info.txt --publish-at 2026-11-20T15:00:00Z

Requirements: pip install -r requirements.txt
Credentials:  gizli/client_secret.json (OAuth desktop client) and gizli/token.json
              (created once by `python uretim/baglan.py`; scopes youtube.upload + youtube.readonly).
"""
from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import sys

import youtube_api


def main() -> int:
    ap = argparse.ArgumentParser(description="Upload and schedule one video on the owner's channel.")
    ap.add_argument("video", type=pathlib.Path, help="mp4 file to upload")
    ap.add_argument("--title", required=True, help="video title (max 100 characters)")
    ap.add_argument("--description-file", type=pathlib.Path, help="UTF-8 text file with the description")
    ap.add_argument("--publish-at", help="RFC 3339 UTC time, e.g. 2026-11-20T15:00:00Z (omit to keep the video private)")
    a = ap.parse_args()

    if not a.video.is_file():
        print(f"File not found: {a.video}", file=sys.stderr)
        return 1
    if a.publish_at:
        zaman = dt.datetime.fromisoformat(a.publish_at.replace("Z", "+00:00"))
        if zaman <= dt.datetime.now(dt.timezone.utc):
            print("--publish-at must be in the future", file=sys.stderr)
            return 1
    aciklama = a.description_file.read_text(encoding="utf-8") if a.description_file else ""

    yt = youtube_api.servis()                      # OAuth 2.0 credentials of the channel owner
    kanal = youtube_api.kanal_bilgisi(yt)          # channels.list(mine=True): confirms the target channel
    print(f"Channel: {kanal['ad']} ({kanal['id']})")
    video_id = youtube_api.video_yukle(yt, a.video, a.title, aciklama, a.publish_at)  # videos.insert
    print(f"Uploaded: https://youtu.be/{video_id}")
    print(f"Scheduled for {a.publish_at}" if a.publish_at else "Visibility: private")
    print(f"Studio: https://studio.youtube.com/video/{video_id}/edit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
