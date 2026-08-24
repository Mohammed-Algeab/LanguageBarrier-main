"""Contract tests for the SGHD single-line harakat stripper.

The production helper is intentionally conservative: it copies SC3 glyph pairs,
line-break/control bytes that have known one-byte form, and the 0xFF 0xFF
terminator. It returns the original string for 0x04, truncated input, or a
missing terminator because those forms need the game's evaluator/parser.
"""

from __future__ import annotations


TERMINATOR = b"\xff\xff"
SINGLE_TERMINATOR = b"\xff"


def strip_harakat(data: bytes, harakat_ids: set[int], max_length: int = 0) -> bytes | None:
    """Return stripped bytes, or None when the production helper must fall back."""
    if max_length > 0:
        scan_limit = max_length * 2 + 256
    else:
        scan_limit = 65536
    out = bytearray()
    index = 0
    changed = False
    while index < scan_limit and index < len(data):
        first = data[index]
        if first == 0x04:
            return None
        if first == 0xFF:
            out.append(first)
            if index + 1 < scan_limit and index + 1 < len(data) and data[index + 1] == 0xFF:
                out.append(data[index + 1])
            return bytes(out) if changed else None
        if first in (0x00, 0x09, 0x0B, 0x1E):
            out.append(first)
            index += 1
            continue
        if (first & 0x80) == 0:
            return None
        if index + 1 >= scan_limit or index + 1 >= len(data):
            return None
        glyph_id = data[index + 1] | ((first & 0x7F) << 8)
        if glyph_id in harakat_ids:
            changed = True
        else:
            out.extend(data[index : index + 2])
        index += 2
    return None


def glyph(glyph_id: int) -> bytes:
    return bytes((0x80 | ((glyph_id >> 8) & 0x7F), glyph_id & 0xFF))


def main() -> None:
    base_a = glyph(0x0123)
    mark = glyph(0x0321)
    base_b = glyph(0x0456)
    source = base_a + mark + base_b + TERMINATOR
    assert strip_harakat(source, {0x0321}) == base_a + base_b + TERMINATOR

    source_with_controls = b"\x09" + base_a + b"\x00" + mark + b"\x0b" + base_b + TERMINATOR
    assert strip_harakat(source_with_controls, {0x0321}) == (
        b"\x09" + base_a + b"\x00" + b"\x0b" + base_b + TERMINATOR
    )

    # No mark means production code leaves the caller's original pointer in place.
    assert strip_harakat(base_a + TERMINATOR, {0x0321}) is None
    assert strip_harakat(base_a + mark + base_b + SINGLE_TERMINATOR, {0x0321}) == (
        base_a + base_b + SINGLE_TERMINATOR
    )
    # Unknown controls and malformed input must never be rewritten.
    assert strip_harakat(b"\x04\x12\x34" + source, {0x0321}) is None
    assert strip_harakat(b"\x12" + source, {0x0321}) is None
    assert strip_harakat(base_a + mark, {0x0321}) is None
    assert strip_harakat(base_a + b"\x80", {0x0321}) is None


if __name__ == "__main__":
    main()
    print("SGHD harakat-strip contract tests: OK")
