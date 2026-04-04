#!/usr/bin/env python

import os
from openai import OpenAI
from pathlib import Path
import sys

usage="youtube-audio-to-text somevideo.web"

#
# If create_output_file is True, this will generate a .txt file based on the .mp3 filename (appends ".txt")
# returns the transcription text
#
def to_text(mp3_filename, api_key, create_output_file=True):
    client = OpenAI(api_key=api_key)

    with open(mp3_filename, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )

        if create_output_file:
            Path(mp3_filename + ".txt").write_text(transcription.text)

        return transcription.text

if __name__ == "__main__":
    if len(sys.argv) < 2:
      print(usage)
      sys.exit(1)

    with open("openai.apikey", encoding="utf-8") as f:
        apikey = f.read()

        for i in range(1, len(sys.argv)):
            to_text(sys.argv[i], apikey)
