"""LOT06 isolated capture validation: bounded PNG structure, fail closed otherwise.

A MIME magic prefix or .ready digest is NOT structural decoding. The synthetic
bridge only approves common 8-bit non-interlaced PNG; JPEG, WebP and PDF must
wait for separate fully tested decoders before clinical use.
"""
from __future__ import annotations
import struct
import zlib

MAX_DECODED_BYTES = 64 * 1024 * 1024
MAX_PIXELS = 16_000_000


def valid_png(data: bytes) -> bool:
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return False
    pos, count, started, has_data, ended = 8, 0, False, False, False
    compressed = bytearray()
    stride = height = 0
    while pos < len(data):
        if pos + 12 > len(data):
            return False
        count += 1
        if count > 4096:
            return False
        length = struct.unpack_from(">I", data, pos)[0]
        end = pos + length + 12
        if end > len(data):
            return False
        kind = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        if zlib.crc32(kind + body) != struct.unpack_from(">I", data, end - 4)[0]:
            return False
        if not started and kind != b"IHDR":
            return False
        if kind == b"IHDR":
            if started or pos != 8 or length != 13:
                return False
            width, height, depth, color, comp, filt, interlace = struct.unpack(
                ">IIBBBBB", body
            )
            channels = {0: 1, 2: 3, 4: 2, 6: 4}.get(color)
            if (channels is None or depth != 8 or comp != 0 or filt != 0
                    or interlace != 0 or not width or not height
                    or width * height > MAX_PIXELS):
                return False
            stride = 1 + width * channels
            if height * stride > MAX_DECODED_BYTES:
                return False
            started = True
        elif kind == b"IDAT":
            if not started or ended:
                return False
            has_data = True
            compressed.extend(body)
            if len(compressed) > 50 * 1024 * 1024:
                return False
        elif kind == b"IEND":
            if not has_data or length or end != len(data):
                return False
            ended = True
            break
        elif not (kind[0] & 32):
            return False  # Reject unknown critical chunks, including PLTE.
        pos = end
    if not ended:
        return False
    try:
        decoder = zlib.decompressobj()
        data_raw = decoder.decompress(compressed, height * stride + 1)
        if decoder.unconsumed_tail or len(data_raw) > height * stride:
            return False
        data_raw += decoder.flush(height * stride + 1 - len(data_raw))
    except (zlib.error, ValueError):
        return False
    if (not decoder.eof or decoder.unused_data or decoder.unconsumed_tail
            or len(data_raw) != height * stride):
        return False
    return all(data_raw[i * stride] in range(5) for i in range(height))


def validated_mime(data: bytes, mime: str | None) -> bool:
    return mime == "image/png" and valid_png(data)
