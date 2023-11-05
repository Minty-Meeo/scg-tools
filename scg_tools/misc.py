# SPDX-License-Identifier: CC0-1.0

from __future__ import annotations
from os import makedirs
from pathlib import Path
from typing import IO, BinaryIO

# Python's read methods are stupid.
def read_exact(io: IO, size: int):
    data = io.read(size)
    if len(data) != size:
        raise EOFError()
    return data
#

# Why is peek like this.
def peek_exact(io: IO, size: int):
    data = io.peek(size)[:size]
    if len(data) != size:
        raise EOFError()
    return data
#

# Python is stupid for not having a basic "read until delimiter" method, unless I'm just missing documentation.
def read_c_string(io: BinaryIO):
    size = 0; tellpos = io.tell()
    while io.read(1) != b'\0':
        size += 1
    io.seek(tellpos)
    return io.read(size)
#

def decode_c_string(c_string: bytes, encoding: str = "utf-8", errors: str = "strict") -> str:
    assert b'\0' in c_string
    return c_string[:c_string.find(b'\0')].decode(encoding, errors)
#

def tristrip_walk(callback: function, primitive: list[int]):
    assert len(primitive) >= 3
    step = False
    for i in range(len(primitive) - 2):
        tri = (primitive[i], primitive[i+1+step], primitive[i+2-step]); step = not step
        if tri[0] == tri[1] or tri[1] == tri[2] or tri[0] == tri[2]:
            continue  # Remove degenerate tri
        callback(tri)
#

def tristrip_walk_new(callback: function, position_primitive: list[int], texture_coordinate_primitive: list[int], normal_primitive: list[int]):
    assert len(position_primitive) == len(texture_coordinate_primitive) == len(normal_primitive) and len(position_primitive) >= 3
    step = False
    for i in range(len(position_primitive) - 2):
        tri_pos = (position_primitive[i], position_primitive[i+1+step], position_primitive[i+2-step])
        tri_tex = (texture_coordinate_primitive[i], texture_coordinate_primitive[i+1+step], texture_coordinate_primitive[i+2-step])
        tri_nrm = (normal_primitive[i], normal_primitive[i+1+step], normal_primitive[i+2-step])
        step = not step
        if (tri_pos[0] == tri_pos[1] or tri_pos[1] == tri_pos[2] or tri_pos[0] == tri_pos[2]) and \
           (tri_pos[0] == tri_pos[1] or tri_pos[1] == tri_pos[2] or tri_pos[0] == tri_pos[2]) and \
           (tri_pos[0] == tri_pos[1] or tri_pos[1] == tri_pos[2] or tri_pos[0] == tri_pos[2]):
            continue  # Remove degenerate tri
        callback(tri_pos, tri_tex, tri_nrm)
#

def tristrip_to_tris(primitive: list[int]):
    tris = list()
    tristrip_walk(lambda tri : tris.append(tri), primitive)
    return tris
#

def align_down(value: int, size: int):
    return value - value % size
#

def align_up(value: int, size: int):
    return align_down(value + size - 1, size)
#

def open_helper(file, mode, make_dirs = False, overwrite = True, buffering = -1, encoding = None, errors = None, newline = None, closefd = True, opener = None):
    file = Path(file).resolve()
    if not overwrite and file.exists(): raise FileExistsError
    if make_dirs: makedirs(file.parent, exist_ok=True)
    return open(file, mode, buffering, encoding, errors, newline, closefd, opener)
#
