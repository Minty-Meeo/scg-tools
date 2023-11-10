# Copyright 2023 Bradley G (Minty Meeo)
# SPDX-License-Identifier: MIT

from os import path
from argparse import ArgumentParser

from scg_tools.gsh import GCMesh
from scg_tools.misc import open_helper

def help(progname: str):
    print(f"This command-line utility can convert the GC Mesh format (*.gsh) made by Santa Cruz games.  Results may vary.\n"
          f"Usage: {progname} <*.gsh filepath> [Wavefront OBJ filepath]")
#

def main() -> int:
    parser = ArgumentParser()
    parser.add_argument("-l", "--little-endian",
        action="store_true",
        dest="little_endian",
        help="Switch to little endian mode (very few files require this).")
    parser.add_argument("input",
        action="store",
        help="Input filepath of the GC Mesh file (*.gsh). This option is required.",
        metavar="PATH")
    parser.add_argument("--dump-wavefront-obj",
        action="store",
        dest="obj_path",
        help="Convert to Wavefront OBJ file",
        metavar="PATH")
    
    options = parser.parse_args()

    if not options.input:
        parser.print_help()
        return 1

    print(options.input)
    with open(options.input, "rb") as f:
        gsh = GCMesh.parse("<" if options.little_endian else ">", f)
    print("Skinnings:")
    for skinning in gsh.skinnings:
        print("{:4} {:4} {:2} {:2} {:2} {:4x}".format(skinning.vtx_begin, skinning.vtx_count, skinning.joint_idx_a, skinning.joint_idx_b, skinning.rank, skinning.weight_fxdpnt))
    if options.obj_path:
        with open_helper(options.obj_path, "w", True, True) as f:
            gsh.dump_wavefront_obj(f)
    return 0
#

#
if __name__ == "__main__":
    exit(main())
