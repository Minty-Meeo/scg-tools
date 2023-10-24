# Copyright 2023 Bradley G (Minty Meeo)
# SPDX-License-Identifier: MIT

from __future__ import annotations
from argparse import ArgumentParser
from typing import BinaryIO

from PIL import Image
from scg_tools.ma4 import CHKFMAP, GEOM, GLGM, GCGM, CTEX, Prop, codepage
from scg_tools.misc import open_helper
from scg_tools.tex import decode_psxtexfile, write_psxtexfile
from scg_tools.txg import decode_gcmaterials, parse_gcmaterials

def dump_props_wavefront_obj(props: list[Prop], images: list[Image.Image], directory: str):
    print("prop count: {:d}".format(len(props)))
    print("idx vertexs meshes name")
    for [n, prop] in enumerate(props):
        prop_name = prop.name.decode(codepage)
        print("{:3d} {:7d} {:6d} {:s}".format(n, len(prop.vertexes), len(prop.meshes), prop_name))
        with open_helper(f"{directory}/{prop_name}.obj", "w", True, True) as f:
            prop.dump_wavefront_obj(f)
    
    for [n, image] in enumerate(images):
        with open_helper(f"{directory}/material_{n}.png", "wb", True, True) as f:
            image.save(f)
#

def dump_geom_props_0_wavefront_obj(chkfmap: CHKFMAP, images: list[Image.Image], directory: str):
    geom_chunk: GEOM = chkfmap.at(b'CELS').at(b'GEOM')
    dump_props_wavefront_obj(geom_chunk.props_0, images, directory)
#

def dump_geom_props_1_wavefront_obj(chkfmap: CHKFMAP, images: list[Image.Image], directory: str):
    geom_chunk: GEOM = chkfmap.at(b'CELS').at(b'GEOM')
    dump_props_wavefront_obj(geom_chunk.props_1, images, directory)
#

def dump_geom_props_3_wavefront_obj(chkfmap: CHKFMAP, images: list[Image.Image], directory: str):
    geom_chunk: GEOM = chkfmap.at(b'CELS').at(b'GEOM')
    dump_props_wavefront_obj(geom_chunk.props_3, images, directory)
#

def dump_glgm_props_wavefront_obj(chkfmap: CHKFMAP, images: list[Image.Image], directory: str):
    glgm_chunk: GLGM = chkfmap.at(b'CELS').at(b'GLGM')
    dump_props_wavefront_obj(glgm_chunk.props, images, directory)
#

def dump_gcgm_props_wavefront_obj(chkfmap: CHKFMAP, images: list[Image.Image], directory: str):
    gcgm_chunk: GCGM = chkfmap.at(b'CELS').at(b'GCGM')
    dump_props_wavefront_obj(gcgm_chunk.props, images, directory)
#

def dump_ctex_psxteximage(chkfmap: CHKFMAP, io: BinaryIO):
    ctex_chunk: CTEX = chkfmap.at(b'CELS').at(b'CTEX')
    write_psxtexfile(io, ctex_chunk.textures)
#

def main() -> int:
    parser = ArgumentParser()
    parser.add_argument("-i", "--input",
        action="store",
        type=str,
        dest="input",
        help="Input filepath of the CHKFMAP file (*.ma4). This option is required.",
        metavar="INPUT",
        required=True)
    parser.add_argument("--dump-props-obj",
        action="store",
        type=str,
        dest="props_path",
        help="Dump prop models in the Wavefront OBJ format to a given directory.",
        metavar="PROPS_PATH")
    parser.add_argument("--load-gcmaterials",
        action="store",
        type=str,
        dest="gcmaterials_path",
        help="Load an external GCMaterials file to use for prop model textures.  If not specified, the unused textures found in the CTEX chunk will be loaded.",
        metavar="GCMATERIALS_PATH")
    parser.add_argument("--dump-psxtexfile",
        action="store",
        type=str,
        dest="psxteximage_path",
        help="Dump the PSXteximage file (*.tex) from the CTEX chunk to a given filepath.",
        metavar="PSXTEXIMAGE_PATH")
    options = parser.parse_args()

    ifile_path = options.input

    with open(ifile_path, "rb") as f:
        chkfmap = CHKFMAP(); chkfmap.parse(f)
    
    if options.props_path:
        if options.gcmaterials_path:
            with open(options.gcmaterials_path, "rb") as f:
                images = decode_gcmaterials(parse_gcmaterials(f))
        else:
            ctex_chunk: CTEX = chkfmap.at(b'CELS').at(b'CTEX')
            images = decode_psxtexfile(ctex_chunk.textures)
        # Other prop dump functions seem completely redundant, so we'll just dump the ones used in-game
        dump_gcgm_props_wavefront_obj(chkfmap, images, options.props_path)
        
    if options.psxteximage_path:
        with open_helper(options.psxteximage_path, "wb", True, True) as f:
            dump_ctex_psxteximage(chkfmap, f)

    return 0
#

if __name__ == "__main__":
    exit(main())
