#!/usr/bin/env python3
"""Make product images transparent by removing white regions connected to the edge."""

from argparse import ArgumentParser
from collections import deque
from pathlib import Path

from PIL import Image


def near_white(pixel, threshold, chroma):
    red, green, blue, alpha = pixel
    return alpha > 0 and min(red, green, blue) >= threshold and max(pixel[:3]) - min(pixel[:3]) <= chroma


def edge_background(image, threshold, chroma):
    width, height = image.size
    pixels = image.load()
    mask = bytearray(width * height)
    queue = deque()

    def add(x, y):
        index = y * width + x
        if not mask[index] and near_white(pixels[x, y], threshold, chroma):
            mask[index] = 1
            queue.append((x, y))

    for x in range(width):
        add(x, 0)
        add(x, height - 1)
    for y in range(height):
        add(0, y)
        add(width - 1, y)

    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < width and 0 <= ny < height:
                add(nx, ny)

    return mask


def remove_white_edge(source, target, threshold, chroma):
    image = Image.open(source).convert("RGBA")
    mask = edge_background(image, threshold, chroma)
    pixels = image.load()
    width, height = image.size
    removed = 0
    for index, is_background in enumerate(mask):
        if is_background:
            x, y = index % width, index // width
            red, green, blue, _ = pixels[x, y]
            pixels[x, y] = (red, green, blue, 0)
            removed += 1
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, "PNG", optimize=True)
    return removed


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--threshold", type=int, default=235)
    parser.add_argument("--chroma", type=int, default=30)
    args = parser.parse_args()
    removed = remove_white_edge(args.input, args.output, args.threshold, args.chroma)
    print(f"{args.input} -> {args.output} ({removed} edge pixels removed)")


if __name__ == "__main__":
    main()
