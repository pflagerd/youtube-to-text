#!/usr/bin/env python
import argparse
import os
import subprocess
import sys

def convert_to_mp3(input_filename):
    if os.path.splitext(input_filename)[1].lower() == ".mp3":
        raise ValueError(f"{input_filename} is already an .mp3 file")

    mp3_filename = os.path.splitext(input_filename)[0] + ".mp3"

    if not os.path.exists(mp3_filename):
        subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
             "-i", input_filename, "-vn", "-acodec", "libmp3lame", mp3_filename],
            check=True,
        )

    return mp3_filename

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert one or more files to .mp3 using ffmpeg")
    parser.add_argument("files", nargs="+", help="Files to convert to .mp3")
    args = parser.parse_args()

    had_error = False
    for input_filename in args.files:
        try:
            print(convert_to_mp3(input_filename))
        except (ValueError, subprocess.CalledProcessError) as e:
            print(f"Error converting {input_filename}: {e}", file=sys.stderr)
            had_error = True

    sys.exit(1 if had_error else 0)
