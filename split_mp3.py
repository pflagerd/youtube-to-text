#!/usr/bin/env python
import subprocess
import sys
import json

def get_duration(filepath):
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", filepath],
        capture_output=True, text=True
    )
    info = json.loads(result.stdout)
    return float(info["format"]["duration"])

def split_mp3(filepath, chunk_minutes=15):
    import os
    duration = get_duration(filepath)
    chunk_sec = chunk_minutes * 60
    base, ext = os.path.splitext(filepath)

    i = 0
    start = 0
    while start < duration:
        out_path = f"{base}_part{i+1:03d}.mp3"
        subprocess.run([
            "ffmpeg", "-y", "-i", filepath,
            "-ss", str(start),
            "-t", str(chunk_sec),
            "-c", "copy",
            out_path
        ], check=True)
        print(f"Exported: {out_path}")
        start += chunk_sec
        i += 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python split_mp3.py <file.mp3> [chunk_minutes]")
        sys.exit(1)

    filepath = sys.argv[1]
    minutes = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    split_mp3(filepath, minutes)
