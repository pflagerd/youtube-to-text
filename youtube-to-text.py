#!/usr/bin/env python
import ffmpeg
from ffmpeg import *

import yt_dlp
from urllib.parse import urlparse
import os
import sys

from openai import OpenAI
from pathlib import Path

usage="youtube-to-text.py some-youtube.url"

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
indexOfThing = video_url.find("v=")
if indexOfThing != -1:
    mp4_output_file = video_url[indexOfThing + 2:] + ".mp4"
else:
    mp4_output_file = video_url[video_url.rfind("/") + 1:] + ".mp4"

if not os.path.exists(mp4_output_file):
    download_video(video_url, mp4_output_file)

mp3_output_file = mp4_output_file.replace(".mp4", ".mp3")

import ffmpeg

probe = ffmpeg.probe(mp4_output_file)
duration = float(probe['format']['duration'])
print(f"Video duration: {duration:.2f} seconds")

# Extract audio
if not os.path.exists(mp3_output_file):
    ffmpeg.input(mp4_output_file).output(mp3_output_file, acodec='mp3').run()

api_key = os.environ['API_KEY']
client = OpenAI(api_key=api_key)

audio_file= open(mp4_output_file.replace(".mp4", ".mp3"), "rb")
transcription = client.audio.transcriptions.create(
  model="whisper-1",
  file=audio_file
)

Path(mp3_output_file + ".txt").write_text(transcription.text)
