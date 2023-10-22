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

def tristrip_walk(callback: function, primitive: list[int]):
    assert len(primitive) >= 3
    step = False
    for i in range(len(primitive) - 2):
        tri = (primitive[i], primitive[i+1+step], primitive[i+2-step]); step = not step
        if tri[0] == tri[1] or tri[1] == tri[2] or tri[0] == tri[2]:
            continue  # Remove degenerate tri
        callback(tri)
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
