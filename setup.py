# SPDX-License-Identifier: CC0-1.0

def main():
    from setuptools import setup
    import scg_tools as app

    setup(
        name         = app.__project__,
        version      = app.__version__,
        entry_points = app.__entry_points__,
        packages     = ["scg_tools"]
    )
#

if __name__ == '__main__':
    main()
