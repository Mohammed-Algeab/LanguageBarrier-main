from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from sghd_harakat_filter import filter_or_original, strip_sghd_harakat_sc3  # noqa: E402


def glyph(glyph_id: int) -> bytes:
    """Encode one SC3 two-byte glyph token."""

    assert 0 <= glyph_id <= 0x7EFF
    return bytes([0x80 | (glyph_id >> 8), glyph_id & 0xFF])


class SghdHarakatStripTests(unittest.TestCase):
    def test_removes_two_byte_harakat_tokens_and_keeps_regular_glyphs(self) -> None:
        regular_before = glyph(0x0123)
        kasra = glyph(0x0456)
        regular_after = glyph(0x0789)
        source = regular_before + kasra + regular_after + b"\xff\xff"

        self.assertEqual(
            strip_sghd_harakat_sc3(source, {0x0456}),
            regular_before + regular_after + b"\xff\xff",
        )

    def test_preserves_known_controls_and_terminator(self) -> None:
        source = b"\x09" + glyph(0x0456) + b"\x0b" + glyph(0x0123) + b"\x1e\xff\xff"

        self.assertEqual(
            strip_sghd_harakat_sc3(source, {0x0456}),
            b"\x09" + b"\x0b" + glyph(0x0123) + b"\x1e\xff\xff",
        )

    def test_linebreak_is_preserved_and_following_text_is_scanned(self) -> None:
        source = glyph(0x0123) + b"\x00" + glyph(0x0456) + glyph(0x0789) + b"\xff\xff"

        self.assertEqual(
            strip_sghd_harakat_sc3(source, {0x0456}),
            glyph(0x0123) + b"\x00" + glyph(0x0789) + b"\xff\xff",
        )

    def test_unknown_variable_length_control_keeps_original(self) -> None:
        # 0x04 is evaluated by the game and its byte length is not known here.
        source = glyph(0x0123) + b"\x04\x99\x88" + glyph(0x0456) + b"\xff\xff"

        self.assertIsNone(strip_sghd_harakat_sc3(source, {0x0456}))
        self.assertEqual(filter_or_original(source, {0x0456}), source)

    def test_unknown_positive_control_keeps_original(self) -> None:
        source = glyph(0x0123) + b"\x05\x01" + glyph(0x0456) + b"\xff"

        self.assertEqual(filter_or_original(source, {0x0456}), source)

    def test_no_harakat_returns_original_without_rewriting(self) -> None:
        source = glyph(0x0123) + b"\xff\xff"

        self.assertIsNone(strip_sghd_harakat_sc3(source, {0x0456}))
        self.assertEqual(filter_or_original(source, {0x0456}), source)


if __name__ == "__main__":
    unittest.main()
