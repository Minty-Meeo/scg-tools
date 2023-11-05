# SPDX-License-Identifier: CC0-1.0

__project__      = 'scg_tools'
__version__      = '1.0.0'

__entry_points__ = {
    "console_scripts": [
        "santacruz_tex = scg_tools.santacruz_tex:main",
        "santacruz_txg = scg_tools.santacruz_txg:main",
        "santacruz_ma4 = scg_tools.santacruz_ma4:main",
        "santacruz_gsh = scg_tools.santacruz_gsh:main",
        "TEX2TXG = scg_tools.TEX2TXG:main",
        "MA4COMPARE = scg_tools.MA4COMPARE:main",
        "MA4UNUSEDPROP = scg_tools.MA4UNUSEDPROP:main",
    ],
}

__requires__ = ["PIL", "gclib", "more_itertools"]
