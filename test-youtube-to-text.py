#!/usr/bin/env python
"""
Test driver for youtube-to-text.py.

youtube-to-text.py does all of its work inside `if __name__ == "__main__":`,
so there is nothing importable to unit test directly. These tests instead:

  * run the real script as a subprocess to check argument-handling behavior
    (usage message / exit codes), and
  * drive the script with runpy, substituting fake `download_from_youtube`,
    `extract_mp3s_from_youtube_mp4`, and `audio_to_text` modules via
    sys.modules, to verify the wiring between those steps and the output
    file it writes -- without touching the network, ffmpeg, or the OpenAI API.

Run with:  python test-youtube-to-text.py [--keep-artifacts]
       or: python -m unittest test-youtube-to-text

Pass --keep-artifacts to keep test_known_video_1's generated files in ./tmp
(relative to this file) instead of deleting them when the test ends --
useful for inspecting the downloaded video, split audio, or transcriptions
after a run. Without it, ./tmp is wiped both before and after that test.
"""
import argparse
import filecmp
import runpy
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock

SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPT_PATH = SCRIPT_DIR / "youtube-to-text.py"

KNOWN_VIDEO_ID = "QeDvYObYeiM"
KNOWN_VIDEO_URL = f"https://www.youtube.com/watch?v={KNOWN_VIDEO_ID}"
KNOWN_VIDEO_REFERENCE_DIR = SCRIPT_DIR / "extracts" / KNOWN_VIDEO_ID

TMP_DIR = SCRIPT_DIR / "tmp"
keep_test_artifacts = False  # set by --keep-artifacts, parsed in __main__ below

FAKE_MODULE_NAMES = (
    "download_from_youtube",
    "extract_mp3s_from_youtube_mp4",
    "audio_to_text",
)


def _venv_python():
    # The script's top-level imports (yt_dlp, ffmpeg-python, openai) only
    # live in the project's own .venv, not necessarily on PATH.
    venv_python = SCRIPT_DIR / ".venv" / "bin" / "python"
    return str(venv_python) if venv_python.exists() else sys.executable


class UsageTest(unittest.TestCase):
    """Runs the real script as a subprocess to check argument validation."""

    def _run(self, args):
        with tempfile.TemporaryDirectory() as cwd:
            return subprocess.run(
                [_venv_python(), str(SCRIPT_PATH), *args],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30,
            )

    def test_no_arguments_prints_usage_and_exits_2(self):
        # youtube-to-text.py's argument parsing is argparse now, so a
        # missing required "url" argument is an argparse usage error:
        # printed to stderr, exit code 2.
        result = self._run([])
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage: youtube-to-text.py", result.stderr)
        self.assertIn("url", result.stderr)

    def test_known_video_1(self):
        # Full, real end-to-end run against a known video: downloads the
        # actual mp4, splits/extracts audio with ffmpeg, and transcribes
        # with the real OpenAI Whisper API. It's slow and makes real
        # (billed) API calls, so it is a heavier check than the rest of
        # this suite. Reference artifacts for this video live in
        # extracts/QeDvYObYeiM/ (see KNOWN_VIDEO_REFERENCE_DIR); this test
        # regenerates the same set of files into a scratch directory and
        # compares each one byte-for-byte against its reference copy.
        reference_files = [p for p in KNOWN_VIDEO_REFERENCE_DIR.iterdir() if p.is_file()]
        self.assertTrue(
            reference_files, f"No reference artifacts found in {KNOWN_VIDEO_REFERENCE_DIR}"
        )

        # Start from a clean ./tmp unless the caller asked to keep (and thus
        # reuse) whatever a previous kept run left behind.
        if not keep_test_artifacts and TMP_DIR.exists():
            shutil.rmtree(TMP_DIR)
        TMP_DIR.mkdir(parents=True, exist_ok=True)

        try:
            result = subprocess.run(
                [_venv_python(), str(SCRIPT_PATH), KNOWN_VIDEO_URL],
                cwd=TMP_DIR,
                capture_output=True,
                text=True,
                timeout=3600,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            for reference_file in reference_files:
                generated_file = TMP_DIR / reference_file.name
                self.assertTrue(
                    generated_file.exists(),
                    f"Expected generated artifact {reference_file.name} was not created",
                )
                self.assertTrue(
                    filecmp.cmp(generated_file, reference_file, shallow=False),
                    f"Generated {reference_file.name} does not match the reference copy "
                    f"in {KNOWN_VIDEO_REFERENCE_DIR}",
                )
        finally:
            if keep_test_artifacts:
                print(f"\nKept generated artifacts in {TMP_DIR}")
            else:
                shutil.rmtree(TMP_DIR, ignore_errors=True)


if __name__ == "__main__":
    # unittest.main() parses sys.argv itself and doesn't recognize this
    # flag, so pull it out with parse_known_args and forward the rest
    # (test names, -v, -k, ...) on to unittest untouched. add_help=False so
    # -h/--help still falls through to unittest's own help text.
    arg_parser = argparse.ArgumentParser(add_help=False)
    arg_parser.add_argument("--keep-artifacts", action="store_true")
    known_args, remaining_argv = arg_parser.parse_known_args()

    keep_test_artifacts = known_args.keep_artifacts
    unittest.main(argv=[sys.argv[0]] + remaining_argv)
