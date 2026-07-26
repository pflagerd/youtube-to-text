#!/usr/bin/env python
"""
Test driver for convert_to_mp3.py.

convert_to_mp3.py exposes a plain convert_to_mp3(input_filename) function, so
most of these tests import the module directly and patch out subprocess.run
to check the ffmpeg wiring and the "already an .mp3" / "skip if already
exists" behavior, without ever running ffmpeg for real. The exception is
RealConversionTest, which runs the real script end-to-end against a tiny
ffmpeg-synthesized audio fixture (real ffmpeg, no network needed) and is the
only test here with meaningful timing to log.

Run with:  python test_convert_to_mp3.py [--keep-artifacts]
       or: python -m unittest test_convert_to_mp3

Pass --keep-artifacts to keep RealConversionTest's generated files in ./tmp
(relative to this file) instead of deleting them when the test ends --
useful for inspecting the generated fixture/mp3 after a run. Without it,
./tmp is wiped both before and after that test.
"""
import argparse
import logging
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPT_PATH = SCRIPT_DIR / "convert_to_mp3.py"
LOG_FILE_PATH = SCRIPT_DIR / "test_convert_to_mp3.py.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(LOG_FILE_PATH)],
)
logger = logging.getLogger(__name__)

TMP_DIR = SCRIPT_DIR / "tmp"
keep_test_artifacts = False  # set by --keep-artifacts, parsed in __main__ below

sys.path.insert(0, str(SCRIPT_DIR))
import convert_to_mp3 as ctm


def _venv_python():
    venv_python = SCRIPT_DIR / ".venv" / "bin" / "python"
    return str(venv_python) if venv_python.exists() else sys.executable


def _make_test_fixture(path):
    # A tiny, real, ffmpeg-decodable input -- a 1-second sine wave -- so
    # RealConversionTest can run real ffmpeg without any network access.
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
         "-c:a", "aac", str(path)],
        check=True,
    )


class ConvertToMp3Test(unittest.TestCase):
    """Checks convert_to_mp3's ffmpeg invocation and its "skip if already
    exists" behavior, with subprocess.run patched out so ffmpeg never runs."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def test_invokes_ffmpeg_with_matching_mp3_name(self):
        input_path = Path(self.tmpdir.name) / "clip.mp4"
        input_path.write_bytes(b"fake mp4 data")
        expected_mp3 = str(input_path.with_suffix(".mp3"))

        with patch.object(ctm, "subprocess") as mock_subprocess:
            mp3_filename = ctm.convert_to_mp3(str(input_path))

        self.assertEqual(mp3_filename, expected_mp3)
        mock_subprocess.run.assert_called_once()
        ffmpeg_args = mock_subprocess.run.call_args[0][0]
        self.assertEqual(ffmpeg_args[0], "ffmpeg")
        self.assertIn(str(input_path), ffmpeg_args)
        self.assertIn(expected_mp3, ffmpeg_args)

    def test_skips_ffmpeg_if_mp3_already_exists(self):
        input_path = Path(self.tmpdir.name) / "clip.mp4"
        mp3_path = input_path.with_suffix(".mp3")
        input_path.write_bytes(b"fake mp4 data")
        mp3_path.write_bytes(b"fake mp3 data")

        with patch.object(ctm, "subprocess") as mock_subprocess:
            mp3_filename = ctm.convert_to_mp3(str(input_path))

        self.assertEqual(mp3_filename, str(mp3_path))
        mock_subprocess.run.assert_not_called()

    def test_rejects_mp3_input_without_running_ffmpeg(self):
        input_path = Path(self.tmpdir.name) / "already.mp3"
        input_path.write_bytes(b"fake mp3 data")

        with patch.object(ctm, "subprocess") as mock_subprocess:
            with self.assertRaisesRegex(ValueError, "already an .mp3 file"):
                ctm.convert_to_mp3(str(input_path))

        mock_subprocess.run.assert_not_called()


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
        self.assertIn("usage: convert_to_mp3.py", result.stderr)
        self.assertIn("files", result.stderr)


class RealConversionTest(unittest.TestCase):
    """Full, real end-to-end runs of the script: real ffmpeg, no mocking, no
    network. Slower than the rest of this suite, so it's the only place here
    with timing recorded and logged."""

    def setUp(self):
        if not keep_test_artifacts and TMP_DIR.exists():
            shutil.rmtree(TMP_DIR)
        TMP_DIR.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        if keep_test_artifacts:
            print(f"\nKept generated artifacts in {TMP_DIR}")
        else:
            shutil.rmtree(TMP_DIR, ignore_errors=True)

    def _run_script(self, *args):
        logger.info("Starting convert_to_mp3.py subprocess with args %s", args)
        start_time = time.perf_counter()
        result = subprocess.run(
            [_venv_python(), str(SCRIPT_PATH), *args],
            cwd=TMP_DIR,
            capture_output=True,
            text=True,
            timeout=60,
        )
        elapsed_seconds = time.perf_counter() - start_time
        logger.info(
            "convert_to_mp3.py subprocess finished in %.2f seconds (exit code %s)",
            elapsed_seconds, result.returncode,
        )
        return result

    def test_converts_fixture_to_mp3(self):
        fixture_path = TMP_DIR / "fixture.mp4"
        _make_test_fixture(fixture_path)

        result = self._run_script(str(fixture_path))

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        mp3_path = TMP_DIR / "fixture.mp3"
        self.assertTrue(mp3_path.exists(), f"Expected {mp3_path} to be created")
        self.assertGreater(mp3_path.stat().st_size, 0)

    def test_mixed_batch_reports_error_but_converts_the_rest(self):
        fixture_path = TMP_DIR / "fixture.mp4"
        _make_test_fixture(fixture_path)
        already_mp3_path = TMP_DIR / "already.mp3"
        already_mp3_path.write_bytes(b"not really an mp3, doesn't matter here")

        result = self._run_script(str(already_mp3_path), str(fixture_path))

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("already an .mp3 file", result.stderr)

        mp3_path = TMP_DIR / "fixture.mp3"
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
