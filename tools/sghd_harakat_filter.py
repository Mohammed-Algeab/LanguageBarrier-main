"""Pure-Python model of the conservative SGHD SC3 harakat filter.

This is a static test oracle, not a replacement for the C++ hook. ``None``
means that the caller must keep the original SC3 buffer unchanged because the
input contains no removable mark or a control whose length is not proven.
"""

from __future__ import annotations

from typing import Iterable, Optional


_FIXED_CONTROLS = {0x09, 0x0B, 0x1E}
_MAX_SCAN_BYTES = 0x10000


def strip_sghd_harakat_sc3(
    source: bytes, harakat_glyph_ids: Iterable[int]
) -> Optional[bytes]:
    """Return a filtered SC3 buffer, or ``None`` for safe fallback.

    SC3 glyph tokens are two bytes: a lead byte in ``0x80..0xFE`` followed by
    the low byte. ``0xFF`` is the terminator and an adjacent second ``0xFF`` is
    preserved. The known one-byte controls are preserved. Control ``0x04`` and
    every other positive byte are rejected because their length is not proven
    by the current source.
    """

    marks = {int(glyph_id) for glyph_id in harakat_glyph_ids}
    if any(glyph_id < 0 or glyph_id > 0x7EFF for glyph_id in marks):
        raise ValueError("glyph IDs must be SC3 values in 0..0x7EFF")

    output = bytearray()
    removed = False
    offset = 0
    while offset < min(len(source), _MAX_SCAN_BYTES):
        byte = source[offset]

        if byte == 0xFF:
            output.append(byte)
            if offset + 1 < len(source) and source[offset + 1] == 0xFF:
                output.append(0xFF)
            return bytes(output) if removed else None

        if byte == 0x00:
            output.append(byte)
            offset += 1
            continue

        if byte in _FIXED_CONTROLS:
            output.append(byte)
            offset += 1
            continue

        if byte == 0x04:
            return None

        if byte >= 0x80:
            if offset + 1 >= len(source):
                return None
            glyph_id = ((byte & 0x7F) << 8) | source[offset + 1]
            if glyph_id in marks:
                removed = True
            else:
                output.extend(source[offset : offset + 2])
            offset += 2
            continue

        return None

    return None


def filter_or_original(source: bytes, harakat_glyph_ids: Iterable[int]) -> bytes:
    """Apply the model while implementing the C++ caller's safe fallback."""

    filtered = strip_sghd_harakat_sc3(source, harakat_glyph_ids)
    return source if filtered is None else filtered
