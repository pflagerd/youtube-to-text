#!/usr/bin/env python

import ffmpeg
from openai import OpenAI
from pathlib import Path
import sys

usage="youtube-audio-to-text somevideo.web"

#
# If create_output_file is True, this will generate a .txt file based on the .mp3 filename (appends ".txt")
# returns the transcription text
#
def audio_to_text(filename, api_key, create_output_file=True):
    client = OpenAI(api_key=api_key)

    with open(filename, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )

        if create_output_file:
            Path(filename + ".txt").write_text(transcription.text)

        return transcription.text


if __name__ == "__main__":
    if len(sys.argv) < 2:
      print(usage)
      sys.exit(1)

    with open("openai.apikey", encoding="utf-8") as f:
        apikey = f.read().strip()

        for i in range(1, len(sys.argv)):
            probe = ffmpeg.probe(sys.argv[i])
            duration = float(probe['format']['duration'])
            print(f"Video duration: {duration:.2f} seconds")

            #audio_to_text(sys.argv[i], apikey)
