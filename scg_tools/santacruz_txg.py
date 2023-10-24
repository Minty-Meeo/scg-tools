# Copyright 2023 Bradley G (Minty Meeo)
# SPDX-License-Identifier: MIT

from __future__ import annotations
from argparse import ArgumentParser
from os import path
from sys import argv

from more_itertools import chunked
from PIL import Image
from scg_tools.misc import open_helper
from scg_tools.txg import GCMaterial, parse_gcmaterials, write_gcmaterials

def command_decode(args: list[str]) -> int:
    parser = ArgumentParser(usage = "decode [options]... <index-1> <output-filepath-1> <index-2> <output-filepath-2> ... <index-N> <output-filepath-N>")
    parser.add_argument("-i", "--input",
        action="store",
        type=str,
        dest="input",
        help="Input filepath of the GCMaterials file (*.txg). This option is required.",
        metavar="INPUT",
        required=True)
    parser.add_argument("-o", "--output",
        action="store",
        type=str,
        dest="output",
        help="Output filepath for decoded texture(s). This must contain the wildcard character if the GCMaterials file contains multiple textures.",
        metavar="OUTPUT")
    parser.add_argument("-w", "--wildcard",
        action="store",
        type=str,
        dest="wildcard",
        help="Wildcard character (or sequence) used by the output option. The default is \"*\".",
        metavar="WILDCARD",
        default='*')    
    options, rest = parser.parse_known_args(args)
    
    errands = list[tuple[int, str]]()
    for batch in chunked(rest, 2, True):  # TODO: Python 3.12 replace with batched
        errands.append((int(batch[0], 0), batch[1]))
    ifile_path: str = options.input
    print(ifile_path)
    with open(ifile_path, "rb") as f:
        gcmaterials = parse_gcmaterials(f)
    if len(gcmaterials) == 0:
        return 1
    if options.output:
        ofile_path: str = options.output; wildcard: str = options.wildcard
        if len(gcmaterials) == 1:
            # I'm too lazy to write a good script that accounts for which files have multiple images and which ones don't.  Maybe this is desirable behavior regardless?
            ofile_path = ofile_path.replace(wildcard, "", 1)
            errands.append((0, ofile_path))
        else:
            assert wildcard in ofile_path, "Output filepath does not contain the wildcard character (or sequence)."
            for [n, gcmaterial] in enumerate(gcmaterials):
                errands.append((n, ofile_path.replace(wildcard, str(n), 1)))
    if len(errands) == 0:
        return 0
    print("idx  mode  xfad blend   pad  width height filename")
    for [n, ofile_path] in errands:
        gcmaterial = gcmaterials[n]
        print("{:3} {:5} {:5} {:5} {:5} {:6} {:6} {:s}".format(n, gcmaterial.mode, gcmaterial.xfad, gcmaterial.blend, gcmaterial.pad, gcmaterial.width, gcmaterial.height, ofile_path))
        with open_helper(ofile_path, "wb", make_dirs = True, overwrite = True) as f:
            gcmaterial.decode().save(f)
    return 0
#

def command_encode(args: list[str]) -> int:
    parser = ArgumentParser(usage = "encode [options]... [mode-1] [input-filepath-1] <mode-2> <input-filepath-2> ... <mode-N> <input-filepath-N>\n"
                                    "\n"
                                    "Texture modes inputs are 0 or \"CMPR\", and 1 or \"RGBA32\".")
    parser.add_argument("-o", "--output",
        action="store",
        type=str,
        dest="output",
        help="Output filepath for the GCMaterials file (*.txg). This option is required.",
        metavar="OUTPUT",
        required=True)
    options, rest = parser.parse_known_args(args)

    inputs = list[tuple[int, str]]()
    for [mode, ifile_path] in chunked(rest, 2, True):  # TODO: Python 3.12 replace with batched
        match mode.casefold():
            case "cmpr":
                mode = 0
            case "rgba32":
                mode = 1
            case _:
                mode = int(mode, 0)
        inputs.append((0, ifile_path))
    if len(inputs) == 0:
        parser.print_help()
        return 1
    ofile_path: str = options.output
    
    gcmaterials = list[GCMaterial]()
    for [mode, ifile_path] in inputs:
        with Image.open(ifile_path) as image:
            gcmaterials.append(GCMaterial.encode(image, mode))
    
    with open_helper(ofile_path, "wb", make_dirs = True, overwrite = True) as f:
        write_gcmaterials(f, gcmaterials)
    return 0
#

def help(progname: str) -> None:
    print(f"This command-line utility works with the GCMaterial image format (*.txg) made by Santa Cruz games\n"
          f"Usage: {progname} COMMAND -h\n"
          f"\n"
          f"commands supported: [decode, encode]")
#

def main() -> int:
    progname = path.basename(argv[0])
    if len(argv) < 2:
        help(progname)
        return 1
    command = argv[1]
    args = argv[2:]
    
    match command.casefold():
        case "decode":
            return command_decode(args)
        case "encode":
            return command_encode(args)
    help(progname)
    return 1
#

if __name__ == "__main__":
    exit(main())
