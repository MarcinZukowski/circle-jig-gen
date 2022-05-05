#!/usr/bin/env python3

import argparse
import math
import sys

from utils import Drawer, dbg, inches, unit, unitStr

ANG_90 = 90
ANG_180 = 180

marks = [15, 18, 22.5, 30, 36, 45, 60, 67.5, 72, 75]

def main():
    parser = argparse.ArgumentParser(description='Generate a set of circle cutting templates.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--minRadius', type=str, default="1cm", help='Minimum radius')
    parser.add_argument('--maxRadius', type=str, default="20cm", help='Maximum radius')
    parser.add_argument('--stepSize', type=str, default="1cm", help="Step size")
    parser.add_argument('--inches', action="store_true", help="Use inches are units")
    parser.add_argument('--angles', choices=[ANG_90, ANG_180],
                        help="Shape", default=ANG_90)
    parser.add_argument('--fence', action="store_true", help="Should fence be created")

    args = parser.parse_args()
    inches = args.inches

    minRadius = unit(args.minRadius)
    maxRadius = unit(args.maxRadius)
    stepSize = unit(args.stepSize)
    angles = args.angles
    fence = args.fence

    assert maxRadius >= minRadius, f'maxRadius={maxRadius} minRadius={minRadius}'
    numSteps = (maxRadius - minRadius) / stepSize
    assert numSteps == int(numSteps)
    numSteps = int(numSteps)

    d = Drawer()

    # Print command line
    for idx, arg in enumerate(sys.argv):
        d.text(3, 3 + idx * 3, arg, fs=3, anchor="start", color=d.MARK)

    cx = 10 + maxRadius
    cy = 10 + maxRadius

    for step in range(0, numSteps + 1):
        radius = minRadius + step * stepSize
        dbg(f'stepSize={stepSize}')
        dbg(radius)
        if angles == ANG_90:
            # Draw arc
            d.arc(cx, cy, radius, 45, 45, color=d.CUT, degrees=True, reverse=True)
            textRadius = math.sqrt((radius-stepSize/2) ** 2 / 2)
            d.text(cx + textRadius, cy - textRadius, unitStr(radius), fs=3, color=d.MARK)
            for mark in marks:
                ang = math.radians(mark)
                for (r0, r1, label) in ((radius - stepSize, radius - stepSize + 2, False), (radius, radius - 2, True)):
                    x0 = math.cos(ang) * r0
                    y0 = math.sin(ang) * r0
                    x1 = math.cos(ang) * r1
                    y1 = math.sin(ang) * r1
                    d.line(cx + x0, cy - y0, cx + x1, cy - y1)
                    if label:
                        d.text(cx + x1, cy - y1, mark, fs=2)
            if fence:
                # Draw fences
                #   2---------3
                #    \       /
                # 0---1     4---5
                x0 = radius - stepSize
                y0 = 0
                x1 = x0 + stepSize * 3 / 8
                y1 = y0
                x2 = x0 + stepSize * 2 / 8
                y2 = y0 - stepSize / 8
                x3 = x0 + stepSize * 6 / 8
                y3 = y2
                x4 = x0 + stepSize * 5 / 8
                y4 = y0
                x5 = x0 + stepSize
                y5 = y0
                # Lower fence
                d.line(cx + x0, cy + y0, cx + x1, cy + y1, d.CUT)
                d.line(cx + x1, cy + y1, cx + x2, cy + y2, d.CUT)
                d.line(cx + x2, cy + y2, cx + x3, cy + y3, d.CUT)
                d.line(cx + x3, cy + y3, cx + x4, cy + y4, d.CUT)
                d.line(cx + x4, cy + y4, cx + x5, cy + y5, d.CUT)
                # Left fence
                d.line(cx - y0, cy - x0, cx - y1, cy - x1, d.CUT)
                d.line(cx - y1, cy - x1, cx - y2, cy - x2, d.CUT)
                d.line(cx - y2, cy - x2, cx - y3, cy - x3, d.CUT)
                d.line(cx - y3, cy - x3, cx - y4, cy - x4, d.CUT)
                d.line(cx - y4, cy - x4, cx - y5, cy - x5, d.CUT)
    if fence:
        # Final fences
        x0, y0 = 0, 0
        x1, y1 = 0, 10
        x2, y2 = maxRadius, 10
        x3, y3 = maxRadius, 0
        # Lower
        d.line(cx + x0, cy + y0, cx + x1, cy + y1, d.CUT)
        d.line(cx + x1, cy + y1, cx + x2, cy + y2, d.CUT)
        d.line(cx + x2, cy + y2, cx + x3, cy + y3, d.CUT)
        # Left
        d.line(cx - y0, cy - x0, cx - y1, cy - x1, d.CUT)
        d.line(cx - y1, cy - x1, cx - y2, cy - x2, d.CUT)
        d.line(cx - y2, cy - x2, cx - y3, cy - x3, d.CUT)
    else:
        # Final cut
        d.line(cx, cy, cx + maxRadius, cy, d.CUT)
        d.line(cx, cy, cx, cy - maxRadius, d.CUT)

    print(d.toSVG())


if __name__ == '__main__':
    main()
