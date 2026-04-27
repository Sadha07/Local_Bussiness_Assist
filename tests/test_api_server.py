import unittest

from backend.api_server import _extract_text


class TestApiServerFormatting(unittest.TestCase):
    def test_table_markdown_is_preserved(self):
        raw = """Top picks:\n| Place | Rating |\n|---|---|\n| A | 4.6 |\n| B | 4.4 |"""
        result = {
            "messages": [
                type("Msg", (), {"content": raw})(),
            ]
        }
        out = _extract_text(result)
        self.assertIn("| Place | Rating |", out)
        self.assertIn("|---|---|", out)

    def test_plain_text_extracted(self):
        raw = "No table here."
        result = {
            "messages": [
                type("Msg", (), {"content": raw})(),
            ]
        }
        self.assertEqual(_extract_text(result), raw)


if __name__ == "__main__":
    unittest.main()
