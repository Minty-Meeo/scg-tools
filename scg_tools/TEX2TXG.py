# Copyright 2023 Bradley G (Minty Meeo)
# SPDX-License-Identifier: MIT

from os import path
from sys import argv

from PIL import Image
from scg_tools.misc import open_helper
from scg_tools.santacruz_tex import parse_psxtexfile, decode_psxtexfile_solo
from scg_tools.santacruz_txg import GCMaterial, write_gcmaterials

def help(progname: str) -> None:
    print(f"Converts a PSXteximage file (*.tex) into a GCMaterials file (*.txg) with RGBA32 format textures.\n"
          f"Usage: {progname} [PSXteximage path] [GCMaterials path]")
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
    images = list[Image.Image]()
    for [mode, unk1, unk2, width, height, data, palette] in psx_textures:
        images.append(decode_psxtexfile_solo(mode, data, palette, width, height))
    gcn_textures = list[GCMaterial]()
    for image in images:
        gcn_textures.append(GCMaterial.encode(image, 1))
    with open_helper(txg_path, "wb", make_dirs = True, overwrite = True) as f:
        write_gcmaterials(f, gcn_textures)
#

if __name__ == "__main__":
    exit(main())
