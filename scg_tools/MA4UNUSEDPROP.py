# Copyright 2023 Bradley G (Minty Meeo)
# SPDX-License-Identifier: MIT

from struct import unpack
from sys import argv
from os import path

from scg_tools.ma4 import CHKFMAP, DATA, GCGM, CANM, data_id_translation, codepage
from scg_tools.misc import decode_c_string

def help(progname: str) -> None:
    print(f"Usage: {progname} <MA4 filepath>")
#

def main() -> int:
    if len(argv) < 2:
        help(path.basename(argv[0]))
        return 1
    
    with open(argv[1], "rb") as f:
        chkfmap = CHKFMAP(); chkfmap.parse(f)
    
    data_chunk: DATA = chkfmap.at(b'MAP_').at(b'DATA')
    gcgm_chunk: GCGM = chkfmap.at(b'CELS').at(b'GCGM')
    canm_chunk: CANM = chkfmap.at(b'CELS').at(b'CANM')

    data_found = set[int]()
    for id in data_chunk.data:
        data_found.add(data_id_translation(id))
    
    canm_found = dict[int, list[str]]()
    for packet_list in canm_chunk.packet_lists:
        canm_name = decode_c_string(packet_list.at(1), codepage)
        for packet in packet_list:
            if packet.type != 3:
                continue
            id = unpack("<I", packet.data)[0]
            if id not in canm_found:
                canm_found[id] = [canm_name]
            else:
                if canm_name not in canm_found[id]:
                    canm_found[id].append(canm_name)

    longest_prop_name = 0
    for prop in gcgm_chunk.props:
        prop_name = prop.name.decode(codepage)
        longest_prop_name = max(longest_prop_name, len(prop_name))

    print("//////////////////////////////////////////////////////")
    print("FOUND:")
    for [n, prop] in enumerate(gcgm_chunk.props):
        prop_name = prop.name.decode(codepage)
        print("{:3d} {:{}s} {:4s} {}".format(
            n,
            prop_name,
            longest_prop_name,
            "data" if n in data_found else "",
            canm_found[n] if n in canm_found else ""))
    return 0
#

if __name__ == "__main__":
    exit(main())
