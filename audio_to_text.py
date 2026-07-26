#!/usr/bin/env python

import argparse
import ffmpeg
from openai import OpenAI
from pathlib import Path
import split_audio
import sys

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
    parser = argparse.ArgumentParser(description="youtube-audio-to-text")
    parser.add_argument("files", nargs="+", help="Audio/video files to transcribe")
    args = parser.parse_args()

    with open(Path(sys.argv[0]).parent / "openai.apikey", encoding="utf-8") as f:
        apikey = f.read().strip()

        for filename in args.files:
            Path(filename + ".txt").write_text(audio_to_text(split_audio.split_audio(filename), apikey))
