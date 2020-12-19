import io
import unittest

from . import SimpleTee


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
