#!/usr/bin/env python

import ffmpeg
from openai import OpenAI
from pathlib import Path
import split_audio
import sys

usage="youtube-audio-to-text somevideo.web"

#
# If create_output_file is True, this will generate a .txt file based on the .mp3 filename (appends ".txt")
# returns the transcription text
#
def audio_to_text(filenames, api_key):
    transcriptions : str = ""
    for filename in filenames:
        print("Extracting text from " + filename)
        client = OpenAI(api_key=api_key)

        with open(filename, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )

            transcription_filename = filename + ".txt"
            print("Writing transcription to " + transcription_filename)
            Path(transcription_filename).write_text(transcription.text)

            transcriptions += " " + transcription.text
    return transcriptions

if __name__ == "__main__":
    if len(sys.argv) < 2:
      print(usage)
      sys.exit(1)

    with open(Path(sys.argv[0]).parent / "openai.apikey", encoding="utf-8") as f:
        apikey = f.read().strip()

        for i in range(1, len(sys.argv)):
            Path(sys.argv[i] + ".txt").write_text(audio_to_text(split_audio.split_audio(sys.argv[i]), apikey))
