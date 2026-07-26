#!/usr/bin/env python
import argparse
import ffmpeg
import os

# noinspection PyShadowingNames
def split_audio(filepath, chunk_minutes=15):
    probe = ffmpeg.probe(filepath)
    duration = float(probe['format']['duration'])
    print(f"Audio duration: {duration:.2f} seconds")

    def frange(start, stop, step):
        # noinspection PyShadowingNames
        startTime = start
        while startTime < stop:
            yield startTime
            startTime += step

    audio_chunk_filepaths = []
    if duration <= 15 * 60.0:
        audio_chunk_filepaths.append(filepath)
    else:
        for startTime in frange(0.0, duration, chunk_minutes * 60.0):
            root, ext = os.path.splitext(filepath)
            audio_chunk_filepath = f"{root}{"-" + str(startTime)}{ext}"
            audio_chunk_filepaths.append(audio_chunk_filepath)
            if not os.path.exists(audio_chunk_filepath):
                ffmpeg.input(filepath, ss=startTime).output(audio_chunk_filepath, t=15 * 60 + 1).run()
    return audio_chunk_filepaths

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split an audio file into fixed-length chunks.")
    parser.add_argument("filepath", help="Path to the audio file")
    parser.add_argument(
        "chunk_minutes", nargs="?", type=int, default=15, help="Chunk length in minutes (default: 15)"
    )
    args = parser.parse_args()

    print(split_audio(args.filepath, args.chunk_minutes))
