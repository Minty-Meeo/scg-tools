# Copyright 2023 Bradley G (Minty Meeo)
# SPDX-License-Identifier: MIT

from sys import argv
from os import path

from scg_tools.ma4 import CHKFMAP, Chunk

def get(chkfmap: CHKFMAP, tid1: bytes, tid2: bytes | None = None) -> Chunk | None:
    try:
        return chkfmap.at(tid1).at(tid2) if tid2 else chkfmap.at(tid1)
    except IndexError:
        return None
#

def print_missing(tid: str, a: Chunk | None, b: Chunk | None) -> bool:
    if a and b:
        return False
    elif a and not b:
        print(f"CHKFMAP B is missing < {tid} >")
    elif not a and b:
        print(f"CHKFMAP A is missing < {tid} >")
    else:
        print(f"CHKFMAP A and B are both missing < {tid} >")
    return True
#

def compare_chunk(chkfmap_a: CHKFMAP, chkfmap_b: CHKFMAP, tid1: bytes, tid2: bytes) -> None:
    a: Chunk | None = get(chkfmap_a, tid1, tid2)
    b: Chunk | None = get(chkfmap_b, tid1, tid2)
    tid_s = tid2.decode() if tid2 else tid1.decode()
    if print_missing(tid_s, a, b): return
    print(f"< {tid_s} > A {'==' if a == b else '!='} < {tid_s} > B")
#

def help(progname: str) -> None:
    print(f"Usage: {progname} <MA4 filepath A> <MA4 filepath B>")
#

def main() -> int:
    if len(argv) < 3:
        help(path.basename(argv[0]))
        return 1
    
    chkfmap_a = CHKFMAP(); chkfmap_a.parse(open(argv[1], "rb"))
    chkfmap_b = CHKFMAP(); chkfmap_b.parse(open(argv[2], "rb"))

    print("//////////////////////////////////////////////////////")
    print("COMPARISON:")
    compare_chunk(chkfmap_a, chkfmap_b, b'GRUV', None   )
    print()
    # MAP_ : HEAD, DATA, NAME, PATH, VARS, ACTI
    compare_chunk(chkfmap_a, chkfmap_b, b'MAP_', b'HEAD')
    compare_chunk(chkfmap_a, chkfmap_b, b'MAP_', b'DATA')
    compare_chunk(chkfmap_a, chkfmap_b, b'MAP_', b'NAME')
    compare_chunk(chkfmap_a, chkfmap_b, b'MAP_', b'PATH')
    compare_chunk(chkfmap_a, chkfmap_b, b'MAP_', b'VARS')
    compare_chunk(chkfmap_a, chkfmap_b, b'MAP_', b'ACTI')
    print()
    # CELS : GEOM, GLGM, GCGM, CTEX, CATR, CANM
    compare_chunk(chkfmap_a, chkfmap_b, b'CELS', b'GEOM')
    compare_chunk(chkfmap_a, chkfmap_b, b'CELS', b'GLGM')
    compare_chunk(chkfmap_a, chkfmap_b, b'CELS', b'GCGM')
    compare_chunk(chkfmap_a, chkfmap_b, b'CELS', b'CTEX')
    compare_chunk(chkfmap_a, chkfmap_b, b'CELS', b'CATR')
    compare_chunk(chkfmap_a, chkfmap_b, b'CELS', b'CANM')

    return 0
#

if __name__ == "__main__":
    exit(main())
