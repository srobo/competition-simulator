import io
import sys
import tempfile
import unittest
import contextlib
from pathlib import Path
from unittest import mock

from . import REPO_ROOT, SimpleTee, tee_streams


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
