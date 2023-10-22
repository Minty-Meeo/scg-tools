# Copyright 2023 Bradley G (Minty Meeo)
# SPDX-License-Identifier: MIT

from os import makedirs
from pathlib import Path
from typing import BinaryIO

from .ma4 import CHKFMAP, GEOM, GLGM, GCGM, CTEX, Prop, codepage
from .misc import open_helper
from .tex import decode_psxtexfile_solo, write_psxtexfile

def dump_props_wavefront_obj(chkfmap: CHKFMAP, props: list[Prop], outdir: Path, basename: str):
    makedirs(outdir, exist_ok=True)
    assert outdir.is_dir()

    chkfmap.dump_texs(outdir, basename + "material_")
    print("prop count: {:d}".format(len(props)))
    print("idx vertexs meshes name")
    for [n, prop] in enumerate(props):
        prop_name = prop.name.decode(codepage)
        print("{:3d} {:7d} {:6d} {:s}".format(n, len(prop.vertexes), len(prop.meshes), prop_name))
        with open(outdir.joinpath(basename + prop_name + ".obj"), "w") as objf:
            prop.dump_wavefront_wavefront_obj(objf)
#

def dump_geom_props_0_wavefront_obj(chkfmap: CHKFMAP, outdir: Path, basename: str):
    geom_chunk: GEOM = chkfmap.at(b'CELS').at(b'GEOM')
    dump_props_wavefront_obj(chkfmap, geom_chunk.props_0, outdir, basename)
#

def dump_geom_props_1_wavefront_obj(chkfmap: CHKFMAP, outdir: Path, basename: str):
    geom_chunk: GEOM = chkfmap.at(b'CELS').at(b'GEOM')
    dump_props_wavefront_obj(chkfmap, geom_chunk.props_1, outdir, basename)
#

def dump_geom_props_3_wavefront_obj(chkfmap: CHKFMAP, outdir: Path, basename: str):
    geom_chunk: GEOM = chkfmap.at(b'CELS').at(b'GEOM')
    dump_props_wavefront_obj(chkfmap, geom_chunk.props_3, outdir, basename)
#

def dump_glgm_props_wavefront_obj(chkfmap: CHKFMAP, outdir: Path, basename: str):
    glgm_chunk: GLGM = chkfmap.at(b'CELS').at(b'GLGM')
    dump_props_wavefront_obj(chkfmap, glgm_chunk.props, outdir, basename)
#

def dump_gcgm_props_wavefront_obj(chkfmap: CHKFMAP, outdir: Path, basename: str):
    gcgm_chunk: GCGM = chkfmap.at(b'CELS').at(b'GCGM')
    dump_props_wavefront_obj(chkfmap, gcgm_chunk.props, outdir, basename)
#

def dump_ctex_psxteximage(chkfmap: CHKFMAP, io: BinaryIO):
    ctex_chunk: CTEX = chkfmap.at(b'CELS').at(b'CTEX')
    write_psxtexfile(io, ctex_chunk.textures)
#

def dump_texs(chkfmap: CHKFMAP, outdir: Path, basename: str):
    makedirs(outdir, exist_ok=True)
    assert outdir.is_dir()
    
    ctex_chunk: CTEX = chkfmap.at(b'CELS').at(b'CTEX')
    print("tex count: {:d}".format(len(ctex_chunk.textures)))
    print("idx  mode  unk1  unk2  width height")
    for [n, [mode, unk1, unk2, width, height, data, palette]] in enumerate(ctex_chunk.textures):
        print("{:3d} {:5d} {:5d} {:5d} {:6d} {:6d}".format(n, mode, unk1, unk2, width, height))
        image = decode_psxtexfile_solo(mode, data, palette, width, height)
        with open(outdir.joinpath(basename + str(n) + ".png"), "wb") as outfile:
            image.save(outfile, "png")
#

def help(progname: str):
    print("Help message\n"
          "Usage: {:s} [CHKFMAP filepath]".format(progname))
#

def main():
    from sys import argv
    from os import path

    if len(argv) < 2:
        help(path.basename(argv[0]))
        return 1
    infile_path = Path(argv[1])
    # outdir_path = Path("./props")
    
    print(infile_path)
    with open(infile_path, "rb") as f:
        test = CHKFMAP(); test.parse(f)
        with open_helper("./test.txe", "wb", True, True) as f:
            test.dump_ctex_psxteximage(f)
        # with open("./test.ma4", "wb") as of:
        #     test.write(of)
        # test.dump_gcgm_props_obj(Path("./gcgm_props"), "")
        # test.dump_glgm_props_obj(Path("./glgm_props"), "")
        # test.dump_geom_props_0_obj(Path("./geom_props/0"), "")
        # test.dump_geom_props_1_obj(Path("./geom_props/1"), "")
        # test.dump_geom_props_3_obj(Path("./geom_props/3"), "")
    return 0
#

if __name__ == "__main__":
    exit(main())
