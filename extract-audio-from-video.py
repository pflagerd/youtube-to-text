#!/usr/bin/env python
import ffmpeg
import os
import sys

usage = "extract-audio-from-video some.mp4"

if len(sys.argv) != 2:
    print(usage)
    sys.exit(1)

file_extension = os.path.splitext(sys.argv[1])[1]

probe = ffmpeg.probe(mp4_output_file)
duration = float(probe['format']['duration'])
print(f"Video duration: {duration:.2f} seconds")

# Extract audio
(
    ffmpeg
    .input(sys.argv[1])  # Input video file
    .output(sys.argv[1].replace(file_extension, ".mp3"), acodec='libmp3lame')  # Output file with audio codec set to mp3
    .run()
)
