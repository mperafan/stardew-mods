#!/usr/bin/env python3
"""Recolor Sebastian's walking sprites: red hair + brown eyes.

Usage: python3 scripts/recolor.py <input.png> <output.png>

How it works
------------
The sheet is a grid of 16x32 px frames. Sebastian's hair and hoodie share the
same dark-purple palette, so a plain color swap would turn his hoodie red too.
Instead, for each frame we find the bottom of his face (the last row with 2+
skin pixels) and only recolor dark pixels ABOVE that line. Back-view frames
have no face, so they fall back to DEFAULT_CHIN_ROW.

Hair colors are mapped by brightness onto a red ramp, so the original shading
(dark outline -> highlights) is kept. Eye colors are swapped 1:1 for browns.
"""
import sys
from PIL import Image

FRAME_W, FRAME_H = 16, 32
DEFAULT_CHIN_ROW = 14  # used when a frame shows no face (back view)

SKIN = {(255, 189, 132), (247, 143, 109), (216, 99, 101)}

# Original eye color -> brown replacement. The white highlight is kept.
EYES = {
    (135, 139, 221): (122, 72, 38),  # front-view iris (blue-ish)
    (94, 99, 19): (101, 58, 30),     # side-view iris (olive)
    (61, 58, 0): (66, 36, 18),       # walking-frame pupil (dark olive)
}
EYE_WHITE = (214, 216, 255)
# This purple is both a hair highlight AND part of the front-view iris.
# When it touches the eye white, it's iris.
SHARED_IRIS = (70, 51, 108)
SHARED_IRIS_BROWN = (88, 50, 26)


def touches_eye_white(px, x, y, w, h):
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < w and 0 <= ny < h and px[nx, ny][:3] == EYE_WHITE:
            return True
    return False

# Dark-to-light red ramp the hair gets mapped onto.
RED_RAMP = [(62, 8, 12), (112, 20, 18), (160, 40, 24), (204, 72, 36), (232, 112, 56)]


def luminance(c):
    r, g, b = c[:3]
    return 0.299 * r + 0.587 * g + 0.114 * b


def is_hair_color(c):
    """Sebastian's hair palette: dark purples (blue/red channels >= green)."""
    r, g, b = c[:3]
    return luminance(c) < 75 and b >= g and r >= g


def ramp(t):
    """Interpolate RED_RAMP at t in [0, 1]."""
    t = max(0.0, min(1.0, t)) * (len(RED_RAMP) - 1)
    i = min(int(t), len(RED_RAMP) - 2)
    f = t - i
    a, b = RED_RAMP[i], RED_RAMP[i + 1]
    return tuple(round(a[k] + (b[k] - a[k]) * f) for k in range(3))


FACE_HEIGHT = 4  # rows from the top of the face down to the chin
FACE_SEARCH_ROWS = 18  # faces are always in the upper part; lower skin = hands


def chin_row(px, fx, fy):
    """Chin = first row with 2+ skin pixels, plus the face height.

    We anchor on the FIRST face row (not the last skin row) because in some
    frames his hands are near his face, and those skin pixels would otherwise
    push the 'chin' down into the hoodie.
    """
    for y in range(FACE_SEARCH_ROWS):
        skin = sum(1 for x in range(FRAME_W) if px[fx + x, fy + y][:3] in SKIN
                   and px[fx + x, fy + y][3] > 0)
        if skin >= 2:
            return y + FACE_HEIGHT - 1
    return DEFAULT_CHIN_ROW


def main(src, dst):
    im = Image.open(src).convert("RGBA")
    px = im.load()

    # Brightness range of the hair palette, used to place colors on the ramp.
    lums = [luminance(p) for p in im.getdata() if p[3] > 0 and is_hair_color(p)]
    lo, hi = min(lums), max(lums)

    for fy in range(0, im.height, FRAME_H):
        for fx in range(0, im.width, FRAME_W):
            chin = chin_row(px, fx, fy)
            for y in range(FRAME_H):
                for x in range(FRAME_W):
                    p = px[fx + x, fy + y]
                    if p[3] == 0:
                        continue
                    if p[:3] in EYES:
                        px[fx + x, fy + y] = EYES[p[:3]] + (p[3],)
                    elif p[:3] == SHARED_IRIS and touches_eye_white(
                            px, fx + x, fy + y, im.width, im.height):
                        px[fx + x, fy + y] = SHARED_IRIS_BROWN + (p[3],)
                    elif y <= chin and is_hair_color(p):
                        t = (luminance(p) - lo) / (hi - lo)
                        px[fx + x, fy + y] = ramp(t) + (p[3],)

    im.save(dst)
    print(f"wrote {dst}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
