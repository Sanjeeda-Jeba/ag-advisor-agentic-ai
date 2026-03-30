"""Tests for CDMS direct HTML label discovery (before Tavily fallback)."""

import os
import unittest
from unittest.mock import patch

from src.cdms.cdms_direct_search import (
    CDMSDirectLabelSearch,
    try_direct_cdms_search,
)


class TestCDMSDirectSearch(unittest.TestCase):
    def test_try_direct_disabled_returns_none(self):
        with patch.dict(os.environ, {"CDMS_DIRECT_SEARCH": "false"}, clear=False):
            self.assertIsNone(try_direct_cdms_search("Roundup", max_results=3))

    def test_try_direct_finds_pdf_from_html(self):
        html = (
            '<html><body>'
            '<a href="https://www.cdms.net/ldat/ldROUND01.pdf">Roundup specimen</a>'
            "</body></html>"
        )
        with patch.dict(
            os.environ, {"CDMS_DIRECT_USE_PLAYWRIGHT": "false"}, clear=False
        ):
            with patch.object(CDMSDirectLabelSearch, "_fetch_html", return_value=html):
                out = try_direct_cdms_search("Roundup", max_results=3)
                self.assertIsNotNone(out)
                assert out is not None
                self.assertTrue(out.get("success"))
                self.assertGreaterEqual(out.get("result_count", 0), 1)
                urls = [r["url"] for r in out.get("results", [])]
                self.assertIn("https://www.cdms.net/ldat/ldROUND01.pdf", urls)
                self.assertEqual(out.get("source"), "CDMS (direct)")

    def test_try_direct_no_pdf_returns_none(self):
        html = "<html><body><p>No links here</p></body></html>"
        with patch.dict(
            os.environ, {"CDMS_DIRECT_USE_PLAYWRIGHT": "false"}, clear=False
        ):
            with patch.object(CDMSDirectLabelSearch, "_fetch_html", return_value=html):
                out = try_direct_cdms_search("Sevin", max_results=3)
        self.assertIsNone(out)

    def test_tile_rank_prefers_closer_product_name(self):
        from src.cdms.cdms_playwright_search import _rank_tiles

        tiles = [
            "2% Sevin® Bait\nWilbur-Ellis",
            "Sevin® 4F\nNovaSource",
            "Sevin® XLR Plus\nNovaSource",
        ]
        ranked = _rank_tiles("Sevin 4F", None, tiles)
        self.assertEqual(ranked[0][0], 1)

    def test_cdms_query_variants_hyphenate_space(self):
        from src.cdms.cdms_playwright_search import _cdms_product_query_variants

        v = _cdms_product_query_variants("hydrovant fa")
        self.assertIn("hydrovant-fa", v)
        self.assertIn("hydrovant fa", v)


if __name__ == "__main__":
    unittest.main()
