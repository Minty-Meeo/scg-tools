# Copyright 2023 Bradley G (Minty Meeo)
# SPDX-License-Identifier: MIT

from __future__ import annotations
from struct import unpack, pack
from typing import BinaryIO

from PIL import Image
from .misc import read_exact

class PSXTexFileError(Exception):
    pass
#

def bgr555_le_decode(data: bytes) -> list[tuple[int]]:
    colors = list[tuple[int]]()
    for i in range(0, len(data), 2):
        bits = unpack("<H", data[i:i+2])[0]
        colors.append(pack("BBB", ((bits & 31) * 255 // 31), (bits >> 5 & 31) * 255 // 31, (bits >> 10 & 31) * 255 // 31))
        assert bits >> 15 == 0, "Non-zero most-significant bit in BGR555 data. Is it alpha?"
    return colors
#

def decode_mode0(data: bytes, palette: bytes, width: int, height: int) -> Image.Image:
    # Only the first 32 bytes of the palette are initialized.
    clut = bgr555_le_decode(palette[:32])
    image = bytearray()
    for i in data:
        image.extend(clut[i      & 15])
        image.extend(clut[i >> 4 & 15])
    return Image.frombytes("RGB", (width, height), image)
#

def decode_mode1(data: bytes, palette: bytes, width: int, height: int) -> Image.Image:
    clut = bgr555_le_decode(palette)
    image = bytearray()
    for i in data:
        image.extend(clut[i])
    return Image.frombytes("RGB", (width, height), image)
#

def decode_mode2(data: bytes, width: int, height: int) -> Image.Image:
    image = b''.join(bgr555_le_decode(data))
    return Image.frombytes("RGB", (width, height), image)
#

def decode_mode3(data: bytes, width: int, height: int) -> Image.Image:
    return Image.frombytes("RGBA", (width, height), data)
#

def decode_psxtexfile_solo(mode: int, data: bytes, palette: bytes, width: int, height: int) -> Image.Image:
    match mode:
        case 0:
            return decode_mode0(data, palette, width, height)
        case 1:
            return decode_mode1(data, palette, width, height)
        case 2:
            return decode_mode2(data, width, height)
        case 3:
            return decode_mode3(data, width, height)
        case _:
            raise PSXTexFileError("Unknown texture format: {:d}.".format(mode))
#

def decode_psxtexfile(psxtexfile: list[int, bytes, bytes, int, int]) -> list[Image.Image]:
    images = list[Image.Image]()
    for [mode, data, palette, width, height] in psxtexfile:
        images.append(decode_psxtexfile_solo(mode, data, palette, width, height))
    return images
#


def parse_psxtexfile_solo(io: BinaryIO):
    # (In the MSVC Debug Runtime, uninitialized data contains bytes of 0xCC)
    # Most of the time, unk1 is zero.  Sometimes, unk1 is uninitialized.  unk2 often increments
    # with each texture, though it can't decide whether it's zero-indexed or not.  There is one
    # example in "/files/models/teeter/el1.tex" where unk2 skips from four to six.  Other times,
    # unk2 can either be 0xFFFF (implying it is signed) or uninitialized.
    [mode, unk1, unk2, width, height] = unpack("<bbhHH", read_exact(io, 8))
    palette = read_exact(io, 512)  # Still exists even if it's not used.
    match mode:
        case 0:  # 4-bit paletted little-endian BGR555 (1/2 byte per pixel)
            return (mode, unk1, unk2, width, height, read_exact(io, width * height // 2), palette)
        case 1:  # 8-bit paletted little-endian BGR555 (1 byte per pixel)
            return (mode, unk1, unk2, width, height, read_exact(io, width * height), palette)
        case 2:  # Full color little-endian BGR555 (2 bytes per pixel)
            return (mode, unk1, unk2, width, height, read_exact(io, width * height * 2), palette)
        case 3:  # Full color 8-bit RGB (4 bytes per pixel)
            return (mode, unk1, unk2, width, height, read_exact(io, width * height * 4), palette)
        case _:
            raise PSXTexFileError("Unknown texture format: {:d}.".format(mode))
#

def parse_psxtexfile(io: BinaryIO):
    textures = list[tuple]()
    try:
        while True: textures.append(parse_psxtexfile_solo(io))
    except EOFError:
        pass
    return textures
#

def write_psxtexfile_solo(io: BinaryIO, mode: int, unk1: int, unk2: int, width: int, height: int, data: bytes, palette: bytes):
    io.write(pack("<bbhHH", mode, unk1, unk2, width, height))
    io.write(palette)
    io.write(data)
#

def write_psxtexfile(io: BinaryIO, textures: list[tuple]):
    for [mode, unk1, unk2, width, height, data, palette] in textures:
        write_psxtexfile_solo(io, mode, unk1, unk2, width, height, data, palette)
#
