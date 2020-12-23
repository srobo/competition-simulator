import io
import sys
import json
import random
import string
import tempfile
import unittest
import contextlib
from typing import IO, Iterator
from pathlib import Path
from unittest import mock

from . import (
    MatchData,
    NUM_ZONES,
    REPO_ROOT,
    SimpleTee,
    Resolution,
    tee_streams,
    read_match_data,
    RecordingConfig,
    record_arena_data,
    record_match_data,
)


def fake_tla() -> str:
    return ''.join(random.choices(string.ascii_uppercase, k=3))


@contextlib.contextmanager
def mock_match_file() -> Iterator[IO[str]]:
    with tempfile.NamedTemporaryFile(suffix='.json', mode='r+t') as f:
        with mock.patch('controller_utils.get_match_file', return_value=Path(f.name)):
            yield f


class TestRepoRoot(unittest.TestCase):
    def test_repo_root_contains_git_dir(self) -> None:
        # A really simple test case to catch silly errors we've hit multiple
        # times where moving the file which computes REPO_ROOT is not paired
        # with an update to it. We therefore use a separate mechanism to
        # validate that our computation is correct -- that the directory
        # contains a `.git` directory.
        git_dir = REPO_ROOT / '.git'
        self.assertTrue(git_dir.exists(), f"{git_dir} should exist")
        self.assertTrue(git_dir.is_dir(), f"{git_dir} should be a directory")


class TestSimpleTee(unittest.TestCase):
    def test_passes_content_through(self) -> None:
        out1 = io.StringIO()
        out2 = io.StringIO()

        tee = SimpleTee(out1, out2)
        tee.write("Bees\n")
        tee.write("Jam\n")
        tee.write("Spam")

        self.assertEqual(
            "Bees\nJam\nSpam",
            out1.getvalue(),
            "First stream has wrong content",
        )

        self.assertEqual(
            "Bees\nJam\nSpam",
            out2.getvalue(),
            "Second stream has wrong content",
        )

    def test_prefix_on_newline(self) -> None:
        out = io.StringIO()

        tee = SimpleTee(out, prefix='@')

        tee.write("Bees\n")
        self.assertEqual(
            "@Bees\n",
            out.getvalue(),
            "Stream has wrong content after first line",
        )

        tee.write("Foo")

        self.assertEqual(
            "@Bees\n@Foo",
            out.getvalue(),
            "Stream has wrong content after starting second line",
        )

        tee.write("\n")

        self.assertEqual(
            "@Bees\n@Foo\n",
            out.getvalue(),
            "Stream has wrong content after completing second line",
        )

        tee.write("\nABC")

        self.assertEqual(
            "@Bees\n@Foo\n@\n@ABC",
            out.getvalue(),
            r"Stream has wrong content after content with leading '\n'",
        )

        tee.write("Three\nFour\n")

        self.assertEqual(
            "@Bees\n@Foo\n@\n@ABCThree\n@Four\n",
            out.getvalue(),
            "Stream has wrong content after adding content containing newlines",
        )

    def test_tee_streams(self) -> None:
        # 'tee_streams' is designed to be used as part of one-shot processes, so
        # it does some otherwise slightly unusual things. As a result we need to
        # also do some slightly odd things to test it.
        with tempfile.NamedTemporaryFile(mode='w+t') as f:
            with contextlib.redirect_stdout(io.StringIO()) as new_stdout:
                with contextlib.redirect_stderr(io.StringIO()) as new_stderr:
                    # Fake the opening of the log file to avoid a leaked file
                    # reference (and associated warning).
                    with mock.patch('pathlib.Path.open', return_value=f):
                        tee_streams(Path(f.name), prefix='prefix:')

                    print('To Stdout')  # noqa:T001
                    print('To Stderr', file=sys.stderr)  # noqa:T001

            self.assertEqual(
                'prefix:To Stdout\n',
                new_stdout.getvalue(),
                "Should have still sent the output to the 'real' stdout",
            )

            self.assertEqual(
                'prefix:To Stderr\n',
                new_stderr.getvalue(),
                "Should have still sent the output to the 'real' stderr",
            )

            f.seek(0)
            self.assertEqual(
                'prefix:To Stdout\nprefix:To Stderr\n',
                f.read(),
                "Should have sent all to the log file",
            )


class TestMatchDataIO(unittest.TestCase):
    def fake_match_data(self) -> MatchData:
        number = 42
        teams = [None, *(fake_tla() for _ in range(NUM_ZONES - 1))]
        random.shuffle(teams)

        recording_config = RecordingConfig(
            Resolution(random.randint(0, 1920), random.randint(0, 1080)),
            quality=random.randint(0, 100),
        )

        return MatchData(
            number,
            teams,
            duration=180,
            recording_config=recording_config,
        )

    def setUp(self) -> None:
        super().setUp()
        ctx = mock_match_file()
        self.match_file = ctx.__enter__()
        self.addCleanup(lambda: ctx.__exit__(None, None, None))

    def test_round_trip(self) -> None:
        match_data = self.fake_match_data()

        record_match_data(match_data)
        read_data = read_match_data()

        self.assertEqual(
            match_data,
            read_data,
            "Wrong data read back out",
        )

    def test_no_recording_config(self) -> None:
        match_data = self.fake_match_data()
        match_data_dict = match_data._asdict()
        match_data_dict['recording_config'] = None
        match_data = MatchData(**match_data_dict)

        record_match_data(match_data)
        read_data = read_match_data()

        self.assertEqual(
            match_data,
            read_data,
            "Wrong data read back out",
        )

    def test_record_arena_data(self) -> None:
        match_data = self.fake_match_data()

        record_match_data(match_data)

        record_arena_data({'foop': ['spam']})

        raw_data = json.load(self.match_file)
        self.assertEqual(
            {'foop': ['spam']},
            raw_data['arena_zones']['other'],
            "Wrong data read back out",
        )

        read_data = read_match_data()

        self.assertEqual(
            match_data,
            read_data,
            "Should not have modified match data already present in file",
        )
