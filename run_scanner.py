import argparse
import os

import cv2

from scanner import scan


def parse_args():
    base = os.path.dirname(__file__)
    default_image_name = "example.jpg"

    parser = argparse.ArgumentParser(description="Run document scanner on an image")
    parser.add_argument("image_name", nargs="?", default=default_image_name, help="Image filename inside images folder")
    return parser.parse_args()


def main():
    args = parse_args()

    base = os.path.dirname(__file__)
    input_path = os.path.join(base, "images", args.image_name)
    stem, ext = os.path.splitext(args.image_name)
    if not ext:
        ext = ".jpg"
    output_dir = os.path.join(base, "result images")
    output_path = os.path.join(output_dir, f"Result_{stem}{ext}")

    os.makedirs(output_dir, exist_ok=True)

    im = cv2.imread(input_path)
    if im is None:
        print("ERROR: input image not found at", input_path)
        raise SystemExit(1)

    scanned = scan(im)
    ok = cv2.imwrite(output_path, scanned)
    if ok:
        print("Wrote scanned image to", output_path)
    else:
        print("Failed to write output")


if __name__ == "__main__":
    main()
