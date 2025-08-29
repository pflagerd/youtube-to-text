#!/usr/bin/env python
import ffmpeg
import os
import sys

def extract_mp3s(mp4_filename):
    probe = ffmpeg.probe(mp4_filename)
    duration = float(probe['format']['duration'])
    print(f"Video duration: {duration:.2f} seconds")

    def frange(start, stop, step):
        startTime = start
        while startTime < stop:
            yield startTime
            startTime += step

    if duration <= 15 * 60.0:
        mp3_filename = mp4_filename.replace(".mp4", ".mp3")
        if not os.path.exists(mp3_filename):
            ffmpeg.input(mp4_filename).output(mp3_filename, acodec='mp3').run()
        return mp3_filename
    else:
        mp3_filenames = []
        for startTime in frange(0.0, duration, 15 * 60.0):
            mp3_filename = mp4_filename.replace(".mp4", "-" + str(startTime) + ".mp3")
            mp3_filenames.append(mp3_filename)
            if not os.path.exists(mp3_filename):
                ffmpeg.input(mp4_filename, ss=startTime).output(mp3_filename, acodec='libmp3lame', t=15 * 60 + 1).run()

            # (
            #     ffmpeg
            #     .input(sys.argv[1])  # Input video file
            #     .output(sys.argv[1].replace(file_extension, ".mp3"), acodec='libmp3lame')  # Output file with audio codec set to mp3
            #     .run()
            # )
        return mp3_filenames

if __name__ == '__main__':
    usage = "extract-audio-from-video some.mp4"

    if len(sys.argv) != 2:
        print(usage)
        sys.exit(1)

    mp4_filename = sys.argv[1]
    resultingFilenames = extract_mp3s(mp4_filename)
    print(f"Generated {len(resultingFilenames)} mp3 files")
