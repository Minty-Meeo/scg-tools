# Copyright 2023 Bradley G (Minty Meeo)
# SPDX-License-Identifier: MIT

from __future__ import annotations
from sys import argv
from os import makedirs, path

from .tex import parse_psxtexfile, decode_psxtexfile_solo

def help(progname: str):
    print("This command-line utility is able to extract the PSXtexfile image format (*.tex) made by Santa Cruz games\n"
          "Usage: {:s} <PSXtexfile filepath> [output basepath]".format(progname))
#

def main():
    if len(argv) < 2:
        help(path.basename(argv[0]))
        return 1
    infile_path = argv[1]
    basepath = argv[2] if len(argv) > 2 else infile_path

    print(infile_path)
    with open (infile_path, "rb") as f:
        textures = parse_psxtexfile(f)
        makedirs(path.dirname(basepath) if '/' in basepath or '\\' in basepath else ".", exist_ok=True)
        print("idx  mode  unk1  unk2  width height")
        for [n, [mode, unk1, unk2, width, height, data, palette]] in enumerate(textures):
            print("{:3} {:5} {:5} {:5} {:6} {:6}".format(n, mode, unk1, unk2, width, height))
            image = decode_psxtexfile_solo(mode, data, palette, width, height)
            outfile_path = "{:s}{:d}.png".format(basepath, n)
            with open(outfile_path, "wb") as outfile:
                image.save(outfile, "png")
    return 0
#

if __name__ == "__main__":
    exit(main())
