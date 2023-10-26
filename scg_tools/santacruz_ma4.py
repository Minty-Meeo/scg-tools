# Copyright 2023 Bradley G (Minty Meeo)
# SPDX-License-Identifier: MIT

from __future__ import annotations
from argparse import ArgumentParser
from struct import unpack
from typing import BinaryIO, TextIO
import json

from PIL import Image
from scg_tools.ma4 import CHKFMAP, Chunk, GEOM, GLGM, GCGM, CTEX, ACTI, Prop, PacketList, codepage, actor_id_translation
from scg_tools.misc import open_helper
from scg_tools.tex import decode_psxtexfile, write_psxtexfile
from scg_tools.txg import decode_gcmaterials, parse_gcmaterials

def dump_props_wavefront_obj(props: list[Prop], images: list[Image.Image], directory: str) -> None:
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

def dump_geom_props_0_wavefront_obj(chkfmap: CHKFMAP, images: list[Image.Image], directory: str) -> None:
    geom_chunk: GEOM = chkfmap.at(b'CELS').at(b'GEOM')
    dump_props_wavefront_obj(geom_chunk.props_0, images, directory)
#

def dump_geom_props_1_wavefront_obj(chkfmap: CHKFMAP, images: list[Image.Image], directory: str) -> None:
    geom_chunk: GEOM = chkfmap.at(b'CELS').at(b'GEOM')
    dump_props_wavefront_obj(geom_chunk.props_1, images, directory)
#

def dump_geom_props_3_wavefront_obj(chkfmap: CHKFMAP, images: list[Image.Image], directory: str) -> None:
    geom_chunk: GEOM = chkfmap.at(b'CELS').at(b'GEOM')
    dump_props_wavefront_obj(geom_chunk.props_3, images, directory)
#

def dump_glgm_props_wavefront_obj(chkfmap: CHKFMAP, images: list[Image.Image], directory: str) -> None:
    glgm_chunk: GLGM = chkfmap.at(b'CELS').at(b'GLGM')
    dump_props_wavefront_obj(glgm_chunk.props, images, directory)
#

def dump_gcgm_props_wavefront_obj(chkfmap: CHKFMAP, images: list[Image.Image], directory: str) -> None:
    gcgm_chunk: GCGM = chkfmap.at(b'CELS').at(b'GCGM')
    dump_props_wavefront_obj(gcgm_chunk.props, images, directory)
#

def dump_ctex_psxtexfile(chkfmap: CHKFMAP, io: BinaryIO) -> None:
    ctex_chunk: CTEX = chkfmap.at(b'CELS').at(b'CTEX')
    write_psxtexfile(io, ctex_chunk.textures)
#

def remove_bad_actors(chkfmap: CHKFMAP) -> None:
    acti_chunk: ACTI = chkfmap.at(b'MAP_').at(b'ACTI')

    def good_actor(packet_list: PacketList) -> bool:
        id = unpack("<i", packet_list.at(4))[0]
        if id > 0xEFFF:
            return True
        # I elect not to remove actor 9 "key 2", 30 "cop", and 51 "ENV 20" because they can be fixed with file edits and don't afflict any known files.
        return actor_id_translation(id) not in (0, 1, 2, 3, 4, 5, 6, 10, 11, 12, 18, 69)
    #
    
    acti_chunk.actors = list(filter(good_actor, acti_chunk.actors))
#

def chunk_dump_json(chkfmap: CHKFMAP, tid1: bytes, tid2: bytes, io: TextIO):
    chunk: Chunk = chkfmap.at(tid1).at(tid2)
    json.dump(chunk.json_dump(), io, indent="  ")
#

def chunk_load_json(chkfmap: CHKFMAP, tid1: bytes, tid2: bytes, io: TextIO):
    chunk: Chunk = chkfmap.at(tid1).at(tid2)
    chunk.json_load(json.load(io))
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
    parser.add_argument("--old-format-parse",
        action="store_true",
        dest="old_format_parse",
        help="Specify that the CHKFMAP file needs to be parsed with the old vertex attribute format. This is important for Pickles World 2 Levels 1-4.")
    parser.add_argument("--old-format-write",
        action="store_true",
        dest="old_format_write",
        help="Specify that the CHKFMAP file needs to be written with the old vertex attribute format. This is important for Pickles World 2 Levels 1-4.")
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
        dest="psxtexfile_path",
        help="Dump the PSXtexfile (*.tex) from the CTEX chunk to a given filepath.",
        metavar="PSXTEXFILE_PATH")
    parser.add_argument("--remove-bad-actors",
        action="store_true",
        dest="remove_bad_actors",
        help="Remove actors which cause a game crash. This is important for Pickles World 2 Levels 1-2.")
    
    parser.add_argument("--dump-catr-json",
        action="store",
        type=str,
        dest="catr_json_dump_path",
        help="Dump the packet data from the CATR chunk to a JSON file",
        metavar="JSON_PATH")
    parser.add_argument("--dump-canm-json",
        action="store",
        type=str,
        dest="canm_json_dump_path",
        help="Dump the packet data from the CANM chunk to a JSON file",
        metavar="JSON_PATH")
    parser.add_argument("--dump-path-json",
        action="store",
        type=str,
        dest="path_json_dump_path",
        help="Dump the packet data from the PATH chunk to a JSON file",
        metavar="JSON_PATH")
    parser.add_argument("--dump-acti-json",
        action="store",
        type=str,
        dest="acti_json_dump_path",
        help="Dump the packet data from the ACTI chunk to a JSON file",
        metavar="JSON_PATH")
    parser.add_argument("--dump-vars-json",
        action="store",
        type=str,
        dest="vars_json_dump_path",
        help="Dump the packet data from the VARS chunk to a JSON file",
        metavar="JSON_PATH")

    parser.add_argument("--load-catr-json",
        action="store",
        type=str,
        dest="catr_json_load_path",
        help="Load replacement packet data from a JSON file for the CATR chunk.",
        metavar="JSON_PATH")
    parser.add_argument("--load-canm-json",
        action="store",
        type=str,
        dest="canm_json_load_path",
        help="Load replacement packet data from a JSON file for the CANM chunk.",
        metavar="JSON_PATH")
    parser.add_argument("--load-path-json",
        action="store",
        type=str,
        dest="path_json_load_path",
        help="Load replacement packet data from a JSON file for the PATH chunk.",
        metavar="JSON_PATH")
    parser.add_argument("--load-acti-json",
        action="store",
        type=str,
        dest="acti_json_load_path",
        help="Load replacement packet data from a JSON file for the ACTI chunk.",
        metavar="JSON_PATH")
    parser.add_argument("--load-vars-json",
        action="store",
        type=str,
        dest="vars_json_load_path",
        help="Load replacement packet data from a JSON file for the VARS chunk.",
        metavar="JSON_PATH")

    parser.add_argument("-o", "--output",
        action="store",
        type=str,
        dest="output",
        help="Output filepath to write the CHKFMAP file (*.ma4) back out to.",
        metavar="OUTPUT")
    options = parser.parse_args()

    ifile_path = options.input

    # Beware!  Global state!
    if options.old_format_parse:
        Prop.old_format_parse = True
    if options.old_format_write:
        Prop.old_format_write = True

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
        
    if options.psxtexfile_path:
        with open_helper(options.psxtexfile_path, "wb", True, True) as f:
            dump_ctex_psxtexfile(chkfmap, f)

    if options.remove_bad_actors:
        remove_bad_actors(chkfmap)
    
    if options.catr_json_dump_path:
        with open_helper(options.catr_json_dump_path, "w", True, True) as f:
            chunk_dump_json(chkfmap, b'CELS', b'CATR', f)
    if options.canm_json_dump_path:
        with open_helper(options.canm_json_dump_path, "w", True, True) as f:
            chunk_dump_json(chkfmap, b'CELS', b'CANM', f)
    if options.path_json_dump_path:
        with open_helper(options.path_json_dump_path, "w", True, True) as f:
            chunk_dump_json(chkfmap, b'MAP_', b'PATH', f)
    if options.acti_json_dump_path:
        with open_helper(options.acti_json_dump_path, "w", True, True) as f:
            chunk_dump_json(chkfmap, b'MAP_', b'ACTI', f)
    if options.vars_json_dump_path:
        with open_helper(options.vars_json_dump_path, "w", True, True) as f:
            chunk_dump_json(chkfmap, b'MAP_', b'VARS', f)
    
    if options.catr_json_load_path:
        with open(options.catr_json_load_path, "r") as f:
            chunk_load_json(chkfmap, b'CELS', b'CATR', f)
    if options.canm_json_load_path:
        with open(options.canm_json_load_path, "r") as f:
            chunk_load_json(chkfmap, b'CELS', b'CANM', f)
    if options.path_json_load_path:
        with open(options.path_json_load_path, "r") as f:
            chunk_load_json(chkfmap, b'MAP_', b'PATH', f)
    if options.acti_json_load_path:
        with open(options.acti_json_load_path, "r") as f:
            chunk_load_json(chkfmap, b'MAP_', b'ACTI', f)
    if options.vars_json_load_path:
        with open(options.vars_json_load_path, "r") as f:
            chunk_load_json(chkfmap, b'MAP_', b'VARS', f)
    
    if options.output:
        with open_helper(options.output, "wb", True, True) as f:
            chkfmap.write(f)

    return 0
#

if __name__ == "__main__":
    exit(main())
