import io
import json
import random
import string
import tempfile
import unittest
import contextlib
from typing import IO, List, Tuple, Iterator, Optional
from pathlib import Path
from unittest import mock

from . import (
    NUM_ZONES,
    SimpleTee,
    read_match_data,
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


class TestMatchDataIO(unittest.TestCase):
    def fake_match_data(self) -> Tuple[int, List[Optional[str]]]:
        number = 42
        teams = [None, *(fake_tla() for _ in range(NUM_ZONES - 1))]
        random.shuffle(teams)

        return number, teams

    def setUp(self) -> None:
        super().setUp()
        ctx = mock_match_file()
        self.match_file = ctx.__enter__()
        self.addCleanup(lambda: ctx.__exit__(None, None, None))

    def test_round_trip(self) -> None:
        number, teams = self.fake_match_data()

        record_match_data(number, teams)
        read_data = read_match_data()

        self.assertEqual(
            (number, teams),
            read_data,
            "Wrong data read back out",
        )

    def test_record_arena_data(self) -> None:
        number, teams = self.fake_match_data()

        record_match_data(number, teams)

        record_arena_data({'foop': ['spam']})

        raw_data = json.load(self.match_file)
        self.assertEqual(
            {'foop': ['spam']},
            raw_data['other'],
            "Wrong data read back out",
        )

        read_data = read_match_data()

        self.assertEqual(
            (number, teams),
            read_data,
            "Should not have modified match data already present in file",
        )
