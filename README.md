# scg-tools
Some tools written in Python for file formats made by Santa Cruz Games

# Installation
Run the command `pip install "scg-tools @ git+https://github.com/Minty-Meeo/scg-tools.git"`.  It may be necessary to use the `--break-system-packages` option if you are on Linux.  scg-tools is dependent on [Pillow](https://pypi.org/project/Pillow/), [more-itertools](https://pypi.org/project/more-itertools/), and [gclib](https://github.com/LagoLunatic/gclib/tree/master)

# Usage
This package comes with the following entrypoints and modules:
```
santacruz_ma4 - command-line tool for working with the CHKFMAP format (*.ma4)
santacruz_tex - command-line tool for working with the PSXtexfile format (*.tex)
santacruz_txg - command-line tool for working with the GCMaterials format (*.txg)
santacruz_gsh - command-line tool for working with the GC Mesh format (*.gsh)
santacruz_msh - command-line tool for working with the PC Mesh format (*.msh)
TEX2TXG - command-line tool for converting from PSXtexfile to GCMaterials
MA4COMPARE - command-line tool for comparing CHKFMAP files you suspect may only have minor differences
MA4UNUSEDPROP - command-line script for finding unused props in CHKFMAP files
ma4 - module for handling the CHKFMAP format (*.ma4)
tex - module for handling the PSXtexfile format (*.tex)
txg - module for handling the GCMaterials format (*.txg)
gsh - module for handling the GC Mesh format (*.gsh)
msh - module for handling the PC Mesh format (*.gsh)
misc - module containing some shared code
```
