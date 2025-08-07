#!/usr/bin/env python

import os
from openai import OpenAI
from pathlib import Path
import sys

usage="youtube-audio-to-text somevideo.web"

print(sys.argv)

if len(sys.argv) < 2:
  print(usage)
  sys.exit(1)

api_key = os.environ['API_KEY']
client = OpenAI(api_key=api_key)

for i in range(1, len(sys.argv)):
    with open(sys.argv[i], "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
          model="whisper-1",
          file=audio_file
        )
        Path(sys.argv[i] + ".txt").write_text(transcription.text)
