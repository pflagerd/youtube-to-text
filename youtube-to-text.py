#!/usr/bin/env python

import download_from_youtube
import extract_mp3s_from_youtube_mp4
import mp3_to_text
from pathlib import Path


import sys

apikey = None

if __name__ == "__main__":
    usage="youtube-to-text.py some-youtube.url"

    if len(sys.argv) != 2:
      print(usage)
      sys.exit(1)

    # Example usage
    video_url = sys.argv[1]
    print("Downloading youtube video from " + video_url)
    mp4_filename = download_from_youtube.download_mp4(video_url)

    print("Extracting mp3(s) from " + mp4_filename)
    mp3_filenames = extract_mp3s_from_youtube_mp4.extract_mp3s(mp4_filename)

    with open("openai.apikey", encoding="utf-8") as f:
        apikey = f.read().strip()

    transcription = ""
    if not isinstance(mp3_filenames, list):
        print("Extracting text from " + mp3_filenames)
        transcription = mp3_to_text.to_text(mp3_filenames, apikey)
    else:
        for mp3_filename in mp3_filenames:
            print("Extracting text from " + mp3_filename)
            transcription += " " + mp3_to_text.to_text(mp3_filename, apikey)

    transcription_filename = download_from_youtube.extract_youtube_id_from_url(video_url) + ".txt"
    print("Writing transcription to " + transcription_filename)
    Path(transcription_filename).write_text(transcription)
