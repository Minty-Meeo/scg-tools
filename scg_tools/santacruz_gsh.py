# Copyright 2023 Bradley G (Minty Meeo)
# SPDX-License-Identifier: MIT

from sys import argv
from os import path

from scg_tools.gsh import GCMesh
from scg_tools.misc import open_helper

def help(progname: str):
    print(f"This command-line utility can convert the GC Mesh format (*.gsh) made by Santa Cruz games.  Results may vary.\n"
          f"Usage: {progname} <*.gsh filepath> [Wavefront OBJ filepath]")
#

def main() -> int:
    if len(argv) < 2:
        help(path.basename(argv[0]))
        return 1
    print(argv[1])
    with open(argv[1], "rb") as f:
        gsh = GCMesh.parse(f)
    print("Skinnings:")
    for joint in gsh.skinnings:
        print("{:4} {:4} {:2} {:2} {:2} {:4x}".format(joint.vtx_begin, joint.vtx_count, joint.joint_idx_a, joint.joint_idx_b, joint.rank, joint.weight_fxdpnt))
    if len(argv) > 2:
        with open_helper(argv[2], "w", True, True) as f:
            gsh.dump_wavefront_obj(f)
    return 0
#

#
if __name__ == "__main__":
    exit(main())
