# scg-tools
Some tools written in Python for file formats made by Santa Cruz Games

# Installation
Run the command `pip install "scg-tools @ git+https://github.com/Minty-Meeo/scg-tools.git"`.  It may be necessary to use the `--break-system-packages` option if you are on Linux.  scg-tools is dependent on [Pillow](https://pypi.org/project/Pillow/), [more-itertools](https://pypi.org/project/more-itertools/), and [gclib](https://github.com/LagoLunatic/gclib/tree/master)

# Usage
This package comes with the following entrypoints and modules:
```
santacruz_ma4 - entrypoint command-line tool for working with the CHKFMAP format (*.ma4)
santacruz_tex - entrypoint command-line tool for working with the PSXtexfile format (*.tex)
santacruz_txg - entrypoint command-line tool for working with the GCMaterials format (*.txg)
TEX2TXG - entrypoint command-line tool for converting from PSXtexfile to GCMaterials
ma4 - module for handling the CHKFMAP format (*.ma4)
tex - module for handling the PSXtexfile format (*.tex)
txg - module for handling the GCMaterials format (*.txg)
misc - module containing some shared code
```
