#!/usr/bin/env python
import yt_dlp
from urllib.parse import urlparse
import os
import sys

usage="download-from-youtube some-youtube.url"

if len(sys.argv) != 2:
  print(usage)
  sys.exit(1)

def download_mp4(url):
    indexOfThing = url.find("v=")
    if indexOfThing != -1:
        mp4_filename = url[indexOfThing + 2:] + ".mp4"
    else:
        mp4_filename = url[url.rfind("/") + 1:] + ".mp4"

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
    video_url = sys.argv[1]
    print(video_url)
    print(download_mp4(video_url))
