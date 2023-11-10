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
    with open_helper(argv[2], "w", True, True) as f:
        msh.dump_wavefront_obj(f)
    return 0
#

#
if __name__ == "__main__":
    exit(main())
