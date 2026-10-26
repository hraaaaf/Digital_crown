"""Bounded structural PNG verifier for P8. Not a medical-image authenticator."""
import struct
import zlib

_SIGNATURE = bytes.fromhex("89504e470d0a1a0a")

def inspect_png(data):
    if type(data) is not bytes or not (45 <= len(data) <= 64_000_000):
        raise ValueError("PNG source bytes unavailable or oversized")
    if not data.startswith(_SIGNATURE):
        raise ValueError("PNG signature missing")
    pos, dimensions, compressed, finished = 8, None, [], False
    idat_started = idat_ended = False
    for _ in range(4096):
        if pos + 12 > len(data):
            raise ValueError("truncated PNG chunk")
        length = struct.unpack_from(">I", data, pos)[0]
        end = pos + 12 + length
        if end > len(data):
            raise ValueError("PNG chunk exceeds file")
        tag, payload = data[pos+4:pos+8], data[pos+8:pos+8+length]
        crc = struct.unpack_from(">I", data, pos+8+length)[0]
        if zlib.crc32(tag + payload) & 0xffffffff != crc:
            raise ValueError("PNG CRC mismatch")
        if dimensions is None:
            if tag != b"IHDR" or length != 13:
                raise ValueError("IHDR must be first")
            w, h, depth, color, comp, filt, interlace = struct.unpack(">IIBBBBB", payload)
            channels = {0:1, 2:3, 4:2, 6:4}.get(color)
            if (w < 512 or h < 512 or w*h > 25_000_000 or
                channels is None or depth not in (8, 16) or
                comp != 0 or filt != 0 or interlace != 0):
                raise ValueError("unsupported source PNG layout")
            dimensions = (w, h, channels * depth // 8)
        elif tag == b"IHDR":
            raise ValueError("duplicate IHDR")
        if tag == b"IDAT":
            if idat_ended:
                raise ValueError("non-contiguous IDAT chunks")
            idat_started = True
            compressed.append(payload)
        elif idat_started:
            idat_ended = True
        if tag == b"IEND":
            if length or not idat_started or end != len(data):
                raise ValueError("invalid PNG end")
            finished = True
            break
        pos = end
    if not finished:
        raise ValueError("PNG IEND not found")
    width, height, bytes_per_pixel = dimensions
    row_size = 1 + width * bytes_per_pixel
    expected = row_size * height
    decoder = zlib.decompressobj()
    try:
        output = decoder.decompress(b"".join(compressed), expected + 1)
        output += decoder.flush(expected + 1 - len(output))
    except zlib.error as exc:
        raise ValueError("corrupt PNG pixel stream") from exc
    if len(output) != expected or not decoder.eof or decoder.unused_data:
        raise ValueError("PNG pixel stream size invalid")
    if any(output[row * row_size] > 4 for row in range(height)):
        raise ValueError("unsupported PNG row filter")
    return width, height
