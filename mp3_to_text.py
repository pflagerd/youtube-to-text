#!/usr/bin/env python

import os
from openai import OpenAI
from pathlib import Path
import sys

usage="youtube-audio-to-text somevideo.web"

def to_text(mp3_filename):
    api_key = os.environ['API_KEY']
    client = OpenAI(api_key=api_key)

    with open(mp3_filename, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        Path(mp3_filename + ".txt").write_text(transcription.text)
    return mp3_filename + ".txt"

if __name__ == "__main__":
    if len(sys.argv) < 2:
      print(usage)
      sys.exit(1)

    for i in range(1, len(sys.argv)):
        to_text(sys.argv[i])
