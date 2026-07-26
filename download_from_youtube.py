#!/usr/bin/env python
import argparse
import subprocess
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
            'js_runtimes': {'node': {}},  # deno isn't installed here; node is
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    return mp4_filename

def extract_mp3(mp4_filename):
    mp3_filename = os.path.splitext(mp4_filename)[0] + ".mp3"

    if not os.path.exists(mp3_filename):
        subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
             "-i", mp4_filename, "-vn", "-acodec", "libmp3lame", mp3_filename],
            check=True,
        )

    return mp3_filename

# Example usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="download-from-youtube")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--extract-mp3", action="store_true", help="Also extract audio as an .mp3 alongside the .mp4")
    args = parser.parse_args()

    print(args.url)
    mp4_filename = download_mp4(args.url)
    print(mp4_filename)

    if args.extract_mp3:
        print(extract_mp3(mp4_filename))
