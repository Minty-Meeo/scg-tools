# Copyright 2023 Bradley G (Minty Meeo)
# SPDX-License-Identifier: MIT

from __future__ import annotations
from io import BytesIO
from struct import unpack, pack
from typing import BinaryIO

from gclib.texture_utils import decode_image, encode_image
from gclib.gx_enums import ImageFormat
from gclib.fs_helpers import read_all_bytes
from PIL import Image
from scg_tools.misc import read_exact, peek_exact, align_up

# Assert: Maxtextures reached  File: V:/pickles/GAME/gc_pickles/texturemanager.cpp Line 116
# If you ever reach this, you are doing something horribly wrong
Maxtextures = 0x800

class GCMaterial(object):
    def __init__(self, mode: int, xfad: int, blend: int, pad: int, width: int, height: int, data: bytes):
        # These header field names are guessed from the contents of "/files/models/TEX2TXG_log.txt".
        self.mode   = mode   # Is read (8003bb48) as a halfword, meaning xfad technically leaks into it.  However, is shifted and masked (8003f188) for choosing calls to GXInitTexObj such that only the upper 8 bits matter.
        self.xfad   = xfad   # Is read (8003bb50) and then stored in a temporary struct which gets discared.  Due to a bug(?), this also affects texture mode logic starting at 80030740.
        self.blend  = blend  # Could this be related to GXSetBlendMode?  However, it does not trigger a memory breakpoint.
        self.pad    = pad    # Padding? Usually a copy of mode, sometimes is uninitialized when mode is not.  This does not trigger a memory breakpoint.
        self.width  = width
        self.height = height
        self.data   = data
    #

    def decode(self) -> Image.Image:
        return decode_image(BytesIO(self.data), None, ImageFormat.RGBA32 if self.mode else ImageFormat.CMPR, None, None, self.width, self.height)
    #

    @staticmethod
    def encode(image: Image.Image, mode: int):
        width, height = image.size
        data = read_all_bytes(encode_image(image, ImageFormat.RGBA32 if mode else ImageFormat.CMPR, None, 0)[0])
        return GCMaterial(mode, 0, 0, 0, width, height, data)
    #
#

def parse_gcmaterials(io: BinaryIO) -> list[GCMaterial]:
    headers = list[list[int, int, int, int, int, int, int]]()
    while unpack(">i", peek_exact(io, 4))[0] != 0:
        headers.append(unpack(">IBBBBHH", read_exact(io, 12)))
    gcmaterials = list[GCMaterial]()
    for [n, [offset, mode, xfad, blend, pad, width, height]] in enumerate(headers):
        io.seek(offset << 4)
        # (In the MSVC Debug Runtime, uninitialized data contains bytes of 0xCC)
        # Sometimes, the texture mode was left uninitialized by TEX2TXG.  Thankfully, it is always RGBA32 in
        # these cases.  If it were not, it is also possible to guess the mode from the bytes-per-pixel ratio.
        # Still, I cannot place confidence in this code without at least putting in a sanity check, so I've
        # chosen to write this pedantic code even though Pickles is not nearly as cautious.
        data = io.read() if n == len(headers) - 1 else read_exact(io, headers[n+1][0] - offset << 4)
        expected_size = width * height * 4 if mode else width * height // 2  # RGBA32 vs CMPR bpp
        assert expected_size == len(data)
        gcmaterials.append(GCMaterial(mode, xfad, blend, pad, width, height, data))
    if len(gcmaterials) > Maxtextures:
        print("Warning: Maxtextures reached.  Pickles texturemanager will fail.")
    return gcmaterials
#

def decode_gcmaterials(gcmaterials: list[GCMaterial]) -> list[Image.Image]:
    images = list[Image.Image]()
    for gcmaterial in gcmaterials:
        images.append(gcmaterial.decode())
    return images 

def write_gcmaterials(io: BinaryIO, gcmaterials: list[GCMaterial]):
    io.seek(align_up(len(gcmaterials) * 12 + 4, 32))
    offsets = list[int]()
    for gcmaterial in gcmaterials:
        offsets.append(io.tell() >> 4)
        io.write(gcmaterial.data)
    io.seek(0)
    for [offset, gcmaterial] in zip(offsets, gcmaterials):
        io.write(pack(">IBBBBHH", offset, gcmaterial.mode, gcmaterial.xfad, gcmaterial.blend, gcmaterial.pad, gcmaterial.width, gcmaterial.height))
    io.write(pack(">I", 0))
    if len(gcmaterials) > Maxtextures:
        print("Warning: Maxtextures reached.  Pickles texturemanager will fail.")
#
