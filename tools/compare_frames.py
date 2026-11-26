#!/usr/bin/env python3
"""Compare desktop reference frames with frames rendered by the Android build.

Usage: python tools/compare_frames.py DESKTOP_DIR ANDROID_DIR

For every PNG in DESKTOP_DIR, reports the share of pixels that differ by more than a small
tolerance (font antialiasing and alpha rounding differ slightly between SDL and Skia), and writes
a side-by-side image (desktop | android | differences in red) to ANDROID_DIR/../side_by_side/.
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

TOLERANCE = 24  # max per-channel difference still counted as equal


def main():
    desktop_dir, android_dir = sys.argv[1], sys.argv[2]
    out_dir = os.path.join(
        os.path.dirname(os.path.abspath(android_dir)), "side_by_side"
    )
    os.makedirs(out_dir, exist_ok=True)
    pygame.init()
    pygame.display.set_mode((1, 1))
    worst = 0.0
    for name in sorted(os.listdir(desktop_dir)):
        if not name.endswith(".png"):
            continue
        a_path = os.path.join(android_dir, name)
        if not os.path.exists(a_path):
            print(f"{name:28s} MISSING on Android")
            worst = 100.0
            continue
        d = pygame.image.load(os.path.join(desktop_dir, name)).convert()
        a = pygame.image.load(a_path).convert()
        w, h = d.get_size()
        diff = pygame.Surface((w, h))
        diff.blit(d, (0, 0))
        dark = pygame.Surface((w, h))
        dark.set_alpha(160)
        dark.fill((0, 0, 0))
        diff.blit(dark, (0, 0))
        dp = pygame.PixelArray(d)
        ap = pygame.PixelArray(a)
        xp = pygame.PixelArray(diff)
        bad = 0
        for x in range(w):
            for y in range(h):
                c1 = d.unmap_rgb(dp[x, y])
                c2 = a.unmap_rgb(ap[x, y])
                if (
                    abs(c1.r - c2.r) > TOLERANCE
                    or abs(c1.g - c2.g) > TOLERANCE
                    or abs(c1.b - c2.b) > TOLERANCE
                ):
                    bad += 1
                    xp[x, y] = (255, 0, 0)
        del dp, ap, xp
        pct = 100.0 * bad / (w * h)
        worst = max(worst, pct)
        print(f"{name:28s} {pct:6.2f}% pixels differ")
        sheet = pygame.Surface((w * 3, h))
        sheet.blit(d, (0, 0))
        sheet.blit(a, (w, 0))
        sheet.blit(diff, (w * 2, 0))
        pygame.image.save(sheet, os.path.join(out_dir, name))
    print(
        f"worst frame: {worst:.2f}% differing pixels; side-by-side images in {out_dir}"
    )


if __name__ == "__main__":
    main()
