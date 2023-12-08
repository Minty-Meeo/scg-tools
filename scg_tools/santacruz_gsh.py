# Copyright 2023 Bradley G (Minty Meeo)
# SPDX-License-Identifier: MIT

from os import path
from argparse import ArgumentParser

from scg_tools.gsh import GCMesh
from scg_tools.misc import open_helper
from scg_tools.txg import parse_gcmaterials, decode_gcmaterials

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
    parser.add_argument("--load-gcmaterials",
        action="store",
        dest="gcmaterials_path",
        help="Input filepath of the associated GCMaterials file",
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
    print(f"Joints: {len(gsh.joints)}")
    for joint in gsh.joints:
        print("{} {} {}".format(joint[0], joint[1], joint[2]))
    print(f"Skinnings: {len(gsh.skinnings)}")
    for skinning in gsh.skinnings:
        print("{:4} {:4} {:2} {:2} {:2} {:4x}".format(skinning.vtx_begin, skinning.vtx_count, skinning.joint_idx_a, skinning.joint_idx_b, skinning.rank, skinning.weight_fxdpnt))
    if options.obj_path:
        [directory, basename] = path.split(path.abspath(options.obj_path))
        [stemname, ext] = path.splitext(basename)
        with open_helper(options.obj_path, "w", True, True) as f:
            gsh.dump_wavefront_obj(f, stemname)
        if options.gcmaterials_path:
            with open(options.gcmaterials_path, "rb") as f:
                images = decode_gcmaterials(parse_gcmaterials(f))
            for [n, image] in enumerate(images):
                with open_helper(f"{directory}/{stemname}_{n}.png", "wb", True, True) as f:
                    image.save(f)
            with open_helper(f"{stemname}.mtl", "w", True, True) as f:
                for n in range(len(images)):
                    f.write(f"newmtl {stemname}_{n}\n"
                            f"  illum 1\n"  # Color on and Ambient on
                            f"  map_Kd {stemname}_{n}.png\n"  # Texture diffuse
                            f"  map_Ka {stemname}_{n}.png\n"  # Texture ambient
                            # These two do the same thing, it just depends on the implementation which one is used.  Blender uses dissolve.
                            f"  map_Tr {stemname}_{n}.png\n"  # Texture transparency
                            f"  map_d  {stemname}_{n}.png\n") # Texture dissolve
    return 0
#

#
if __name__ == "__main__":
    exit(main())
