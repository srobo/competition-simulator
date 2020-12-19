import io
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
    SimpleTee,
    Resolution,
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
        with mock.patch('controller_utils.MATCH_FILE', new=Path(f.name)):
            yield f


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


@mock_match_file()
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

    def test_record_arena_data(self, match_file: IO[str]) -> None:
        match_data = self.fake_match_data()

        record_match_data(match_data)

        record_arena_data({'foop': ['spam']})

        raw_data = json.load(match_file)
        self.assertEqual(
            {'foop': ['spam']},
            raw_data['other'],
            "Wrong data read back out",
        )

        read_data = read_match_data()

        self.assertEqual(
            match_data,
            read_data,
            "Should not have modified match data already present in file",
        )
