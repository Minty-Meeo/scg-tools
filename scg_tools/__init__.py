# SPDX-License-Identifier: CC0-1.0

__project__      = 'scg_tools'
__version__      = '1.0.0'

__entry_points__ = {
    "console_scripts": [
        "santacruz_tex = scg_tools.santacruz_tex:main",
        "santacruz_txg = scg_tools.santacruz_txg:main",
        "santacruz_ma4 = scg_tools.santacruz_ma4:main",
        "TEX2TXG = scg_tools.TEX2TXG:main",
    ],
}

__requires__ = ["PIL", "gclib", "more_itertools"]
