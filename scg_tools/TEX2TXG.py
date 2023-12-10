# Copyright 2023 Bradley G (Minty Meeo)
# SPDX-License-Identifier: MIT

from os import path
from sys import argv

from scg_tools.misc import open_helper
from scg_tools.santacruz_tex import parse_psxtexfile, decode_psxtexfile_solo
from scg_tools.santacruz_txg import GCMaterial, write_gcmaterials

def help(progname: str) -> None:
    print(f"Converts a PSXtexfile (*.tex) into a GCMaterials file (*.txg) with RGBA32 format textures.\n"
          f"Usage: {progname} [PSXtexfile path] [GCMaterials path]")
#

def main() -> int:
    progname = path.basename(argv[0])
    if len(argv) < 3:
        help(progname)
        return 1
    tex_path = argv[1]
    txg_path = argv[2]

    with open(tex_path, "rb") as f:
        psx_textures = parse_psxtexfile(f)
    
    gcmaterials = list[GCMaterial]()
    for [mode, unk1, unk2, width, height, data, palette] in psx_textures:
        gcmaterials.append(GCMaterial.encode(decode_psxtexfile_solo(mode, data, palette, width, height), unk1))

    with open_helper(txg_path, "wb", make_dirs = True, overwrite = True) as f:
        write_gcmaterials(f, gcmaterials)
#

if __name__ == "__main__":
    exit(main())
