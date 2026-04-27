import unittest

from backend.mcp_client.mcp_client import _normalize_business_id


class TestBusinessIdNormalization(unittest.TestCase):
    def test_accepts_string(self):
        self.assertEqual(_normalize_business_id("abc"), "abc")

    def test_accepts_list_and_uses_first_item(self):
        self.assertEqual(_normalize_business_id(["id-1", "id-2"]), "id-1")

    def test_strips_whitespace(self):
        self.assertEqual(_normalize_business_id("  xyz  "), "xyz")

    def test_rejects_empty_string(self):
        with self.assertRaises(ValueError):
            _normalize_business_id("   ")

    def test_rejects_empty_list(self):
        with self.assertRaises(ValueError):
            _normalize_business_id([])


if __name__ == "__main__":
    unittest.main()
