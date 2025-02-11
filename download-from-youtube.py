#!/usr/bin/env python
import yt_dlp
from urllib.parse import urlparse
import os
import sys

usage="download-from-youtube some-youtube.url"

if len(sys.argv) != 2:
  print(usage)
  sys.exit(1)

def download_video(url, output_path):
    ydl_opts = {
        'format': 'best',
        'outtmpl': output_path,  # Specify the output path and filename
        'quiet': True,           # Run non-interactively without printing to stdout
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

# Example usage
video_url = sys.argv[1]
indexOfThing = video_url.index("v=")
output_file = video_url[indexOfThing + 2:] + ".mp4"
print(video_url)
print(output_file)
download_video(video_url, output_file)
