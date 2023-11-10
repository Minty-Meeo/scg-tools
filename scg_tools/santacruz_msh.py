# Copyright 2023 Bradley G (Minty Meeo)
# SPDX-License-Identifier: MIT

from sys import argv
from os import path

from scg_tools.msh import PCMesh
from scg_tools.misc import open_helper

def help(progname: str):
    print(f"help {progname}")
#

def main() -> int:
    if len(argv) < 2:
        help(path.basename(argv[0]))
        return 1
    print(argv[1])
    with open(argv[1], "rb") as f:
        msh = PCMesh.parse(f)
    print("Skinnings:")
    for skinning in msh.skinnings:
        print("{:4} {:4} {:2} {:2} {:2} {:4x}".format(skinning.vtx_begin, skinning.vtx_count, skinning.joint_idx_a, skinning.joint_idx_b, skinning.rank, skinning.weight_fxdpnt))
    with open_helper(argv[2], "w", True, True) as f:
        msh.dump_wavefront_obj(f)
    return 0
#

#
if __name__ == "__main__":
    exit(main())
