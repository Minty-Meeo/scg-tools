# Copyright 2023 Bradley G (Minty Meeo)
# SPDX-License-Identifier: MIT

from __future__ import annotations
from argparse import ArgumentParser
from os import path
from pathlib import Path
from sys import argv
from typing import BinaryIO

from PIL import Image
from .ma4 import CHKFMAP, GEOM, GLGM, GCGM, CTEX, Prop, codepage
from .misc import open_helper
from .tex import decode_psxtexfile_solo, decode_psxtexfile, write_psxtexfile

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

def dump_geom_props_0_wavefront_obj(chkfmap: CHKFMAP, directory: str):
    geom_chunk: GEOM = chkfmap.at(b'CELS').at(b'GEOM')
    ctex_chunk: CTEX = chkfmap.at(b'CELS').at(b'CTEX')
    props = geom_chunk.props_0; images = decode_psxtexfile(ctex_chunk.textures)
    dump_props_wavefront_obj(chkfmap, props, images, directory)
#

def dump_geom_props_1_wavefront_obj(chkfmap: CHKFMAP, directory: str):
    geom_chunk: GEOM = chkfmap.at(b'CELS').at(b'GEOM')
    ctex_chunk: CTEX = chkfmap.at(b'CELS').at(b'CTEX')
    props = geom_chunk.props_1; images = decode_psxtexfile(ctex_chunk.textures)
    dump_props_wavefront_obj(chkfmap, props, images, directory)
#

def dump_geom_props_3_wavefront_obj(chkfmap: CHKFMAP, directory: str):
    geom_chunk: GEOM = chkfmap.at(b'CELS').at(b'GEOM')
    ctex_chunk: CTEX = chkfmap.at(b'CELS').at(b'CTEX')
    props = geom_chunk.props_3; images = decode_psxtexfile(ctex_chunk.textures)
    dump_props_wavefront_obj(chkfmap, props, images, directory)
#

def dump_glgm_props_wavefront_obj(chkfmap: CHKFMAP, directory: str):
    glgm_chunk: GLGM = chkfmap.at(b'CELS').at(b'GLGM')
    ctex_chunk: CTEX = chkfmap.at(b'CELS').at(b'CTEX')
    props = glgm_chunk.props; images = decode_psxtexfile(ctex_chunk.textures)
    dump_props_wavefront_obj(chkfmap, props, images, directory)
#

def dump_gcgm_props_wavefront_obj(chkfmap: CHKFMAP, directory: str):
    gcgm_chunk: GCGM = chkfmap.at(b'CELS').at(b'GCGM')
    ctex_chunk: CTEX = chkfmap.at(b'CELS').at(b'CTEX')
    props = gcgm_chunk.props; images = decode_psxtexfile(ctex_chunk.textures)
    dump_props_wavefront_obj(chkfmap, props, images, directory)
#

def dump_ctex_psxteximage(chkfmap: CHKFMAP, io: BinaryIO):
    ctex_chunk: CTEX = chkfmap.at(b'CELS').at(b'CTEX')
    write_psxtexfile(io, ctex_chunk.textures)
#

def dump_ctex_decode(chkfmap: CHKFMAP, ofile_path: str, wildcard: str):
    ctex_chunk: CTEX = chkfmap.at(b'CELS').at(b'CTEX')
    print("tex count: {:d}".format(len(ctex_chunk.textures)))
    print("idx  mode  unk1  unk2  width height")
    for [n, [mode, unk1, unk2, width, height, data, palette]] in enumerate(ctex_chunk.textures):
        print("{:3d} {:5d} {:5d} {:5d} {:6d} {:6d}".format(n, mode, unk1, unk2, width, height))
        image = decode_psxtexfile_solo(mode, data, palette, width, height)
        with open_helper(ofile_path.replace(wildcard, str(n), 1), "wb", True, True) as f:
            image.save(f, "png")
#

def main():
    parser = ArgumentParser()
    parser.add_argument("-i", "--input",
        action="store",
        type=str,
        dest="input",
        help="Input filepath of the CHKFMAP file (*.ma4). This option is required.",
        metavar="INPUT",
        required=True)
    parser.add_argument("-w", "--wildcard",
        action="store",
        type=str,
        dest="wildcard",
        help="Wildcard character (or sequence) used by the output options. The default is \"*\".",
        metavar="WILDCARD",
        default='*')
    parser.add_argument("--dump-props-obj",
        action="store",
        type=str,
        dest="props_path",
        help="Dump prop models in the Wavefront OBJ format to a given directory.",
        metavar="PROPS_PATH")
    parser.add_argument("--dump-psxtexfile",
        action="store",
        type=str,
        dest="psxteximage_path",
        help="Dump the PSXteximage file (*.tex) from the CTEX chunk to a given filepath.",
        metavar="PSXTEXIMAGE_PATH")
    options, rest = parser.parse_known_args(argv)
    
    ifile_path = options.input
    wildcard = options.wildcard

    with open(ifile_path, "rb") as f:
        chkfmap = CHKFMAP(); chkfmap.parse(f)
    
    if options.props_path:
        # Other prop dump functions seem completely redundant, so we'll just dump the ones used in-game
        dump_gcgm_props_wavefront_obj(chkfmap, options.props_path)
    
    if options.psxteximage_path:
        with open_helper(options.psxteximage_path, "wb", True, True) as f:
            dump_ctex_psxteximage(chkfmap, f)
    

    return 0
#

if __name__ == "__main__":
    exit(main())
