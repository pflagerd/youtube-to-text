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
indexOfThing = video_url.index("v=")
output_file = video_url[indexOfThing + 2:] + ".mp4"

if not os.path.exists(output_file):
    download_video(video_url, output_file)

file_extension = os.path.splitext(output_file)[1]
mp3_output_file = output_file.replace(file_extension, ".mp3")

import ffmpeg

probe = ffmpeg.probe("input.mp4")
duration = float(probe['format']['duration'])
print(f"Video duration: {duration:.2f} seconds")
print(f"Video duration: {duration:.2f} seconds")


# Extract audio
if not os.path.exists(mp3_output_file):
    ffmpeg.input(output_file).output(mp3_output_file, acodec='mp3').run()

api_key = os.environ['API_KEY']
client = OpenAI(api_key=api_key)

audio_file= open(output_file.replace(file_extension, ".mp3"), "rb")
transcription = client.audio.transcriptions.create(
  model="whisper-1",
  file=audio_file
)

Path(mp3_output_file + ".txt").write_text(transcription.text)
