"""Sum up 19 November 2026 world news in one image.

Writes the bundled news image to /output/entry.png, byte for byte.
No network, no randomness: two runs write identical bytes.
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    src = os.path.join(HERE, "news.jpg")
    if not os.path.isfile(src):
        raise SystemExit("news.jpg is missing next to main.py")
    os.makedirs("/output", exist_ok=True)
    dst = "/output/entry.png"
    shutil.copyfile(src, dst)
    print(f"Wrote {dst} ({os.path.getsize(dst)} bytes)")


if __name__ == "__main__":
    main()
