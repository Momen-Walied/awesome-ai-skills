from __future__ import annotations

import unittest

from app.config import CHUNK_OVERLAP


class IngestionConfigTests(unittest.TestCase):
    def test_chunk_overlap_matches_the_documented_setting(self) -> None:
        self.assertEqual(CHUNK_OVERLAP, 40)


if __name__ == "__main__":
    unittest.main()
