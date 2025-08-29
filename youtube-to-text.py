#!/usr/bin/env python

import download_from_youtube
import extract_mp3s_from_youtube_mp4
import mp3_to_text

import os
import sys

from openai import OpenAI
from pathlib import Path

usage="youtube-to-text.py some-youtube.url"

if len(sys.argv) != 2:
  print(usage)
  sys.exit(1)

# Example usage
video_url = sys.argv[1]
print("Downloading youtube video from " + video_url)
mp4_filename = download_from_youtube.download_mp4(video_url)

mp3_filenames = extract_mp3s_from_youtube_mp4.extract_mp3s(mp4_filename)

if not isinstance(mp3_filenames, list):
    mp3_to_text.to_text(mp3_filenames)
else:
    txt_filenames = []
    for mp3_filename in mp3_filenames:
        print("Extracting text from" + mp3_filename)
        txt_filenames.append(mp3_to_text.to_text(mp3_filename))