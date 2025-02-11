#!/usr/bin/env python

from openai import OpenAI
from pathlib import Path
import sys

usage="youtube-audio-to-text somevideo.web"

print(sys.argv)

if len(sys.argv) != 2:
  print(usage)
  sys.exit(1)

api_key = ""
client = OpenAI(api_key=api_key)

audio_file= open(sys.argv[1], "rb")
transcription = client.audio.transcriptions.create(
  model="whisper-1",
  file=audio_file
)

Path(sys.argv[1] + ".txt").write_text(transcription.text)
