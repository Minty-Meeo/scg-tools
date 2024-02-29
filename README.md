# scg-tools
Some tools written in Python for file formats made by Santa Cruz Games.

## Installation
Run the command `pip install "scg-tools @ git+https://github.com/Minty-Meeo/scg-tools.git"`.  It may be necessary to use the `--break-system-packages` option if you are on Linux.  scg-tools is dependent on [Pillow](https://pypi.org/project/Pillow/), [more-itertools](https://pypi.org/project/more-itertools/), and [gclib](https://github.com/LagoLunatic/gclib/tree/master).

## Entry Points
- `santacruz_ma4`: Command-line tool for working with the CHKFMAP format (\*.ma4).
- `santacruz_tex`: Command-line tool for working with the PSXtexfile format (\*.tex).
- `santacruz_txg`: Command-line tool for working with the GCMaterials format (\*.txg).
- `santacruz_gsh`: Command-line tool for working with the GC Mesh format (\*.gsh).
- `santacruz_msh`: Command-line tool for working with the PC Mesh format (\*.msh).
- `TEX2TXG`: Command-line tool for converting from PSXtexfile to GCMaterials.
- `MA4COMPARE`: Command-line tool for comparing CHKFMAP files you suspect may only have minor differences.
- `MA4UNUSEDPROP`: Command-line script for finding unused props in CHKFMAP files.

## Modules
- `ma4` Library for CHKFMAP format (\*.ma4).
- `tex` Library for PSXtexfile format (\*.tex).
- `txg` Library for GCMaterials format (\*.txg).
- `gsh` Library for GC Mesh format (\*.gsh).
- `msh` Library for PC Mesh format (\*.msh).
