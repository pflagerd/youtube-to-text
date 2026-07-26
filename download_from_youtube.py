#!/usr/bin/env python
import argparse
import yt_dlp
from urllib.parse import urlparse
import os

def extract_youtube_id_from_url(url):
    offset_of_youtube_id = url.find("v=")
    if offset_of_youtube_id != -1:
        return url[offset_of_youtube_id + 2:]
    else:
        return url[url.rfind("/") + 1:]

def download_mp4(url):
    mp4_filename = extract_youtube_id_from_url(url) + ".mp4"

    if not os.path.exists(mp4_filename):
        ydl_opts = {
            'format': 'best',
            'outtmpl': mp4_filename,  # Specify the output path and filename
            'quiet': True,           # Run non-interactively without printing to stdout
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    return mp4_filename

# Example usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="download-from-youtube")
    parser.add_argument("url", help="YouTube video URL")
    args = parser.parse_args()

    print(args.url)
    print(download_mp4(args.url))
