#!/usr/bin/env python3
"""v4 entry: copy the pre-rendered front page to /output/entry.png.

The page itself is v4.jpg, rendered on this machine with PIL and real
TTF fonts (see render_v4.py); this program only copies its bytes, so
two runs always write identical output. Pure standard library.
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    os.makedirs("/output", exist_ok=True)
    src = os.path.join(HERE, "v4.jpg")
    dst = "/output/entry.png"
    shutil.copyfile(src, dst)
    print("Wrote %s (%d bytes)" % (dst, os.path.getsize(dst)))


if __name__ == "__main__":
    main()
