#!/usr/bin/env python
"""
Test driver for download_from_youtube.py.

Unlike youtube-to-text.py, download_from_youtube.py exposes plain functions
(extract_youtube_id_from_url, download_mp4, extract_mp3), so most of these
tests import the module directly and patch out yt_dlp / ffmpeg to check the
wiring -- without touching the network or running ffmpeg for real. The one
exception is KnownVideoTest, which runs the real script end-to-end against a
known, short YouTube video (real download, real ffmpeg) and is the only test
here with meaningful timing to log.

Run with:  python test_download_from_youtube.py [--keep-artifacts]
       or: python -m unittest test_download_from_youtube

Pass --keep-artifacts to keep KnownVideoTest's generated files in ./tmp
(relative to this file) instead of deleting them when the test ends --
useful for inspecting the downloaded mp4/mp3 after a run. Without it, ./tmp
is wiped both before and after that test.
"""
import argparse
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPT_PATH = SCRIPT_DIR / "download_from_youtube.py"
LOG_FILE_PATH = SCRIPT_DIR / "test_download_from_youtube.py.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(LOG_FILE_PATH)],
)
logger = logging.getLogger(__name__)

KNOWN_VIDEO_ID = "QeDvYObYeiM"
KNOWN_VIDEO_URL = f"https://www.youtube.com/watch?v={KNOWN_VIDEO_ID}"

TMP_DIR = SCRIPT_DIR / "tmp"
keep_test_artifacts = False  # set by --keep-artifacts, parsed in __main__ below

sys.path.insert(0, str(SCRIPT_DIR))
import download_from_youtube as dfy


def _venv_python():
    # download_from_youtube.py's top-level import (yt_dlp) only lives in the
    # project's own .venv, not necessarily on PATH.
    venv_python = SCRIPT_DIR / ".venv" / "bin" / "python"
    return str(venv_python) if venv_python.exists() else sys.executable


class ExtractYoutubeIdTest(unittest.TestCase):
    """Pure-function checks -- no network, no subprocess."""

    def test_watch_url(self):
        self.assertEqual(
            dfy.extract_youtube_id_from_url("https://www.youtube.com/watch?v=abc123"),
            "abc123",
        )

    def test_short_url(self):
        self.assertEqual(
            dfy.extract_youtube_id_from_url("https://youtu.be/abc123"),
            "abc123",
        )


class DownloadMp4Test(unittest.TestCase):
    """Checks download_mp4's yt_dlp wiring and its "skip if already exists"
    behavior, with yt_dlp.YoutubeDL patched out so no network call happens."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        original_cwd = os.getcwd()
        os.chdir(self.tmpdir.name)
        self.addCleanup(os.chdir, original_cwd)

    def test_downloads_when_file_missing(self):
        mock_ydl = MagicMock()
        mock_ydl.__enter__.return_value = mock_ydl
        with patch.object(dfy.yt_dlp, "YoutubeDL", return_value=mock_ydl) as mock_ydl_cls:
            mp4_filename = dfy.download_mp4("https://www.youtube.com/watch?v=abc123")

        self.assertEqual(mp4_filename, "abc123.mp4")
        mock_ydl_cls.assert_called_once()
        mock_ydl.download.assert_called_once_with(["https://www.youtube.com/watch?v=abc123"])

    def test_skips_download_if_file_already_exists(self):
        Path("abc123.mp4").write_bytes(b"already here")

        with patch.object(dfy.yt_dlp, "YoutubeDL") as mock_ydl_cls:
            mp4_filename = dfy.download_mp4("https://www.youtube.com/watch?v=abc123")

        self.assertEqual(mp4_filename, "abc123.mp4")
        mock_ydl_cls.assert_not_called()


class ExtractMp3Test(unittest.TestCase):
    """Checks extract_mp3's ffmpeg invocation and its "skip if already
    exists" behavior, with subprocess.run patched out so ffmpeg never runs."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def test_invokes_ffmpeg_with_matching_mp3_name(self):
        mp4_path = Path(self.tmpdir.name) / "abc123.mp4"
        mp4_path.write_bytes(b"fake mp4 data")
        expected_mp3 = str(mp4_path.with_suffix(".mp3"))

        with patch.object(dfy.subprocess, "run") as mock_run:
            mp3_filename = dfy.extract_mp3(str(mp4_path))

        self.assertEqual(mp3_filename, expected_mp3)
        mock_run.assert_called_once()
        ffmpeg_args = mock_run.call_args[0][0]
        self.assertEqual(ffmpeg_args[0], "ffmpeg")
        self.assertIn(str(mp4_path), ffmpeg_args)
        self.assertIn(expected_mp3, ffmpeg_args)

    def test_skips_ffmpeg_if_mp3_already_exists(self):
        mp4_path = Path(self.tmpdir.name) / "abc123.mp4"
        mp3_path = mp4_path.with_suffix(".mp3")
        mp4_path.write_bytes(b"fake mp4 data")
        mp3_path.write_bytes(b"fake mp3 data")

        with patch.object(dfy.subprocess, "run") as mock_run:
            mp3_filename = dfy.extract_mp3(str(mp4_path))

        self.assertEqual(mp3_filename, str(mp3_path))
        mock_run.assert_not_called()


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
        result = self._run([])
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage: download_from_youtube.py", result.stderr)
        self.assertIn("url", result.stderr)


class KnownVideoTest(unittest.TestCase):
    """Full, real end-to-end run against a known video: downloads the actual
    mp4 and, with --extract-mp3, extracts its audio with real ffmpeg. It's
    slow and makes a real network call, so it is a heavier check than the
    rest of this suite."""

    def setUp(self):
        if not keep_test_artifacts and TMP_DIR.exists():
            shutil.rmtree(TMP_DIR)
        TMP_DIR.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        if keep_test_artifacts:
            print(f"\nKept generated artifacts in {TMP_DIR}")
        else:
            shutil.rmtree(TMP_DIR, ignore_errors=True)

    def test_download_and_extract_mp3(self):
        logger.info("Starting download_from_youtube.py subprocess for %s", KNOWN_VIDEO_URL)
        start_time = time.perf_counter()
        result = subprocess.run(
            [_venv_python(), str(SCRIPT_PATH), "--extract-mp3", KNOWN_VIDEO_URL],
            cwd=TMP_DIR,
            capture_output=True,
            text=True,
            timeout=600,
        )
        elapsed_seconds = time.perf_counter() - start_time
        logger.info(
            "download_from_youtube.py subprocess for %s finished in %.2f seconds (exit code %s)",
            KNOWN_VIDEO_URL, elapsed_seconds, result.returncode,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        mp4_path = TMP_DIR / f"{KNOWN_VIDEO_ID}.mp4"
        mp3_path = TMP_DIR / f"{KNOWN_VIDEO_ID}.mp3"

        self.assertTrue(mp4_path.exists(), f"Expected {mp4_path} to be created")
        self.assertGreater(mp4_path.stat().st_size, 0)

        self.assertTrue(mp3_path.exists(), f"Expected {mp3_path} to be created")
        self.assertGreater(mp3_path.stat().st_size, 0)


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
