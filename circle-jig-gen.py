#!/usr/bin/env python3

import argparse
import xml.etree.ElementTree as ET
import math
import sys

svg = ""

SH_NARROW = "narrow"
SH_WIDE = "wide"
SH_RECTANGLE = "rectangle"
SH_LINE = "line"

LAYER_SINGLE = "single"
LAYER_DOUBLE = "double"
LAYER_SUPPORT = "support"

CX = 80
CY = 80

MM2PX = 3.7795

# Screw dimensions - from the center

# Self measured
SCREWS_DEWALT_TRIM = '-30.5mm,-30.5mm,6mm,10mm;-30.5mm,+30.5mm,6mm,10mm;+30.5mm,-30.5mm,6mm,10mm;+30.5mm,+30.5mm,6mm,10mm'

# From https://www.routerforums.com/threads/dw625ek-base-plate.95657/page-2#lg=thread-95657&slide=0
# Definitely wrong
SCREWS_DEWALT_625 = '-57.5mm,-15mm,6mm;57.5mm,-15mm,6mm;0mm,75mm,6mm'

SLIDES_DEFAULT="0,90,180,270,120,240:25mm:47mm:6mm:10mm"


def dbg(s):
    print(str(s), file=sys.stderr)

class Drawer:

    CUT = "red"
    MARK = "blue"
    GUIDE = "green"
    DBG = "#f0f0f0"

    GREEN = "green"
    RED = "red"
    BLUE = "blue"
    ORANGE = "orange"
    NONE = "none"

    def __init__(self, margin=10):
        self.margin = margin
        self.color = self.GREEN
        self.width = 1
        self.fill = self.NONE
        self.content = ""
        self.bounds = [min(CX, 0), min(CY, 0), CX, CY]

    def inc_bounds(self, x, y):
        self.bounds[0] = min(self.bounds[0], x)
        self.bounds[1] = min(self.bounds[1], y)
        self.bounds[2] = max(self.bounds[2], x)
        self.bounds[3] = max(self.bounds[3], y)

    def stroke(self, color=None, width=None):
        color = color or self.color
        width = width or self.width
        fill = self.fill
        s = f'stroke="{color}" fill="{fill}"'
        if width != 1:
            s += f' stroke-width="width"'
        return s

    def line(self, x0, y0, x1, y1, color=None, extra=""):
        self.inc_bounds(x0, y0)
        self.inc_bounds(x1, y1)
        self.content += f'<line x1="{x0}mm" y1="{y0}mm" x2="{x1}mm" y2="{y1}mm" {self.stroke(color)} {extra}/>'

    def cross(self, x, y, size, color=None):
        self.line(x - size, y, x + size, y, color)
        self.line(x, y - size, x, y + size, color)

    def circle(self, x, y, radius, color=None):
        self.inc_bounds(x - radius, y - radius)
        self.inc_bounds(x + radius, y + radius)
        self.content += f'<circle cx="{x}mm" cy="{y}mm" r="{radius}mm" {self.stroke(color)}/>'

    def text(self, x, y, text, color=None, fs=5, anchor="middle", extra=""):
        color = color or self.color
        self.content += f'<text style="font-family:monospace" fill="{color}" x="{x}mm" y="{y}mm" font-size="{fs}mm" text-anchor="{anchor}" {extra}>{text}</text>'

    # Draw an arc
    def arc(self, cx, cy, radius, angle, rot, color=None, reverse=False, degrees=False):
        stroke = self.stroke(color)
        largeArc = 0 if reverse else 1
        ymul = -1 if reverse else 1
        if degrees:
            angle = math.radians(angle)
            rot = math.radians(rot)
        x0 = cx + math.cos(angle + rot) * radius
        y0 = cy + math.sin(angle + rot) * radius * ymul
        x1 = cx + math.cos(-angle + rot) * radius
        y1 = cy + math.sin(-angle + rot) * radius * ymul
        self.content += f"""
            <path d=" M {x0 * MM2PX} {y0 * MM2PX} A {radius * MM2PX} {radius * MM2PX} 0 {largeArc} 1 {x1 * MM2PX} {y1 * MM2PX}" {stroke}/>
        """
        self.inc_bounds(cx - radius, cy - radius)
        self.inc_bounds(cx + radius, cy + radius)

    def write(self):
        minx = self.bounds[0] - self.margin
        miny = self.bounds[1] - self.margin
        maxx = self.bounds[2] + self.margin
        maxy = self.bounds[3] + self.margin
        width = maxx - minx
        height = maxy - miny
        s = f'<svg  version="1.1" xmlns="http://www.w3.org/2000/svg" width="{width}mm" height="{height}mm" viewBox="{minx}mm {miny}mm {maxx}mm {maxy}mm">'
        s += self.content
        s += f'</svg>'

        try:
            elem = ET.fromstring(s)
            ET.indent(elem, space="  ", level=0)
            s = ET.tostring(elem, encoding='utf8', method='xml').decode()
            s = s.replace('ns0:', '').replace(':ns0', '')
            return s
        except ET.ParseError as e:
            print(e)
            print(f"...{s[e.position[1] - 30 : e.position[1] + 30]}...")

        print(f'<!--\n{s}\n-->\n')




def main():
    parser = argparse.ArgumentParser(description='Generate a circle cutting jig.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--minRadius', type=str, default="6in", help='Minimum radius')
    parser.add_argument('--bitDiam', type=str, default="0.25in", help='Bit diameter')
    parser.add_argument('--pinDiam', type=str, default="2mm", help='Pin diameter')
    parser.add_argument('--cutDiam', type=str, default="1in", help='Cut-hole diameter')
    parser.add_argument('--stepSize', type=str, default="1in", help="Major step size")
    parser.add_argument('--steps', type=int, default=6, help="Major step size")
    parser.add_argument('--subSteps', type=int, default=4, help="Number of substeps")
    parser.add_argument('--stepAngle', type=float, default=2, help="Angle between substeps")
    parser.add_argument('--inches', action="store_true", help="Use inches are units")
    parser.add_argument('--shape', choices=[SH_NARROW, SH_RECTANGLE, SH_LINE, SH_WIDE],
                        help="Shape", default=SH_RECTANGLE)
    parser.add_argument('--screws', help="Screw holes positions in format: x0,y0,d0[,D1];x1,y1,d1[,D1]",
                        default=SCREWS_DEWALT_TRIM)
    parser.add_argument('--screwSlides', help="Screw slides in format: angle1[,angleN]:rad1:rad2:diam0[:diam1]",
                        default=SLIDES_DEFAULT)
    parser.add_argument('--bigCircle', type=str, default="2.5in", help="Shape: Big circle radius")
    parser.add_argument('--smallCircle', type=str, default="1in", help="Shape: Small circle radius")
    parser.add_argument('--layers', choices=[LAYER_SINGLE, LAYER_DOUBLE, LAYER_SUPPORT],
                        help="How to arrange layers", default=LAYER_SINGLE)

    args = parser.parse_args()
    inches = args.inches

    # Converts to mm
    def unit(v):
        if v.endswith("mm"):
            return float(v[:-2])
        if v.endswith("in"):
            return float(v[:-2]) * 25.4
        v = float(v)
        if inches:
            return v * 25.4
        return v

    def unitStr(v):
        if v == 0:
            return "0"
        if inches:
            v /= 25.4
            v = round(v * 10000000) / 10000000
            pi = int(v)
            pf = v - pi
            if pf == 0:
                return f"{pi}"
            s = str(v)
            for frac in [2, 4, 8, 16, 32, 64, 128]:
                mu = pf * frac
                if mu == int(mu):
                    s = f"{int(mu)}/{frac}"
                    if pi > 0:
                        s = f"{pi} {s}"
                    return s
            return s
        else:
            v = round(v * 100) / 100
            if v == int(v):
                return str(int(v))
            return str(v)

    minRadius = unit(args.minRadius)
    bitDiam = unit(args.bitDiam)
    bitRadius = bitDiam / 2
    pinDiam = unit(args.pinDiam)
    pinRadius = pinDiam / 2
    cutRadius = unit(args.cutDiam) / 2
    stepSize = unit(args.stepSize)
    steps = args.steps
    subSteps = args.subSteps
    stepAngle = args.stepAngle
    shape = args.shape
    screws = args.screws
    screwSlides = args.screwSlides
    bigCircleRadius = unit(args.bigCircle)
    smallCircleRadius = unit(args.smallCircle)
    layers = args.layers

    d = Drawer()

    # Print command line
    for idx, arg in enumerate(sys.argv):
        d.text(3, 3 + idx * 3, arg, fs=3, anchor="start", color=d.MARK)

    def compRadius(step, subStep):
        return bitRadius + minRadius + step * stepSize + subStep * stepSize / subSteps

    def generatePins(cx, cy, bottom=False):

        def pinHolePosition(step, subStep):
            nonlocal x, y
            ang = subStep * stepAngle - (subSteps - 1) * stepAngle / 2
            angrad = math.radians(ang)
            radius = compRadius(step, subStep)
            if subSteps == 1 or shape == SH_LINE:
                x = radius
                y = 0
            elif shape == SH_RECTANGLE:
                # Draw holes in a rectangle
                substepWidth = 8
                y = (subSteps - 1) * substepWidth / 2 - subStep * substepWidth
                x = math.sqrt(radius * radius - y * y)
            elif shape == SH_WIDE:
                # Draw holes expanding from the bit
                x = math.cos(angrad) * radius
                y = - math.sin(angrad) * radius
            elif shape == SH_NARROW:
                # Draw holes expanding from far away from the bit
                # Math based on
                # https://www.calculator.net/triangle-calculator.html?vc=&vx=20&vy=&va=&vz=60&vb=7&angleunits=d&x=0&y=0
                far = minRadius + (steps - 1) * stepSize * 2
                B = angrad
                c = far
                b = radius
                C = math.pi - math.asin(c * math.sin(B) / b)
                A = math.pi - B - C
                a = b * math.sin(A) / math.sin(B)
                x = far - math.cos(angrad) * a
                y = - math.sin(angrad) * a
            else:
                assert False, f"Unknown shape: {shape}"
            return cx + x, cy + y

        # Holes for the pins
        for step in range(0, steps):
            for subStep in range(0, subSteps):
                x, y = pinHolePosition(step, subStep)
                d.circle(x, y, pinRadius, d.CUT)

        if not bottom:
            # Per-substep/angle guides
            if shape != SH_LINE:
                for subStep in range(0, subSteps):
                    x0, y0 = pinHolePosition(0, subStep)
                    x1, y1 = pinHolePosition(steps - 1, subStep)
                    d.line(x0, y0, x1, y1, d.GUIDE, 'stroke-dasharray="10,10" stroke-width="0.5"')

            # Per-step/major guides
            if shape != SH_LINE:
                for step in range(0, steps):
                    for subStep in range(1, subSteps):
                        x0, y0 = pinHolePosition(step, subStep - 1)
                        x1, y1 = pinHolePosition(step, subStep)
                        d.line(x0, y0, x1, y1, d.GUIDE, 'stroke-dasharray="5, 5" stroke-width="0.25"')

            # Per-step labels
            for step in range(0, steps):
                s = unitStr(minRadius + step * stepSize)
                x, y = pinHolePosition(step, 0)
                d.text(0, 0, s, anchor="end", fs=6, color=d.MARK, extra=f'transform="translate({(x + 2) *3.7795}, {(y + 5)*MM2PX}) rotate(270)"')
                d.line(x, y + 1, x, y + 4, d.MARK)
                if shape != SH_LINE:
                    s = unitStr(minRadius + step * stepSize + (subSteps - 1) * stepSize / subSteps)
                    x, y = pinHolePosition(step, subSteps - 1)
                    d.text(0, 0, s, anchor="start", fs=4, color=d.MARK, extra=f'transform="translate({(x + 2) *3.7795}, {(y - 5)*MM2PX}) rotate(270)"')
                    d.line(x, y - 1, x, y - 4, d.MARK)

            if shape != SH_LINE:
                # Per-angle labels
                if subSteps > 0:
                    for subStep in range(1, subSteps):
                        s = "+" + unitStr(subStep * stepSize / subSteps)
                        x, y = pinHolePosition(0, subStep)
                        d.text(x - 2, y + 1, s, anchor="end", fs=4, color=d.MARK)
                        x, y = pinHolePosition(steps - 1, subStep)
                        d.text(x + 2, y + 1, s, anchor="start", fs=4, color=d.MARK)
            else:
                # Minor tick labels
                for step in range(0, steps):
                    for subStep in range(1, subSteps):
                        x, y = pinHolePosition(step, subStep)
                        s = "+" + unitStr(subStep * stepSize / subSteps)
                        d.text(0, 0, s, anchor="start", fs=3, color=d.MARK,
                               extra=f'transform="translate({(x + 1) * 3.7795}, {(y - 2) * 3.7795}) rotate(270)"')

    def outline(cx, cy):
        # draw shape around
        bcr = bigCircleRadius
        scr = smallCircleRadius
        scd = compRadius(steps, 0)    # small circle distance

        if shape != SH_RECTANGLE:
            # Angle for the line adjactent to two circles
            rd = bcr - scr  # radius difference triangle
            ang = math.acos(rd / scd)
            dbg(ang)

            # Left arc and connection points
            bx = math.cos(ang) * bcr
            by = math.sin(ang) * bcr
            d.circle(cx + bx, cy + by, 1, color=d.DBG)
            d.circle(cx + bx, cy - by, 1, color=d.DBG)
            d.arc(cx, cy, bcr, ang, 0, color=d.CUT)

            # Right arc and connection points
            sx = math.cos(ang) * scr
            sy = math.sin(ang) * scr
            d.circle(cx + scd + sx, cy + sy, 1, color=d.DBG)
            d.circle(cx + scd + sx, cy - sy, 1, color=d.DBG)
            d.arc(cx + scd, cy, scr, ang, 0, color=d.CUT, reverse=1)

            # Connecting lines
            d.line(cx + bx, cy + by, cx + scd + sx, cy + sy, color=d.CUT)
            d.line(cx + bx, cy - by, cx + scd + sx, cy - sy, color=d.CUT)

        else:
            # "Rectangle"
            d.arc(cx, cy, bcr, math.pi / 2, 0, color=d.CUT)
            d.line(cx, cy + bcr, cx + scd + scr, cy + bcr, color=d.CUT)
            d.line(cx, cy - bcr, cx + scd + scr, cy - bcr, color=d.CUT)
            d.line(cx + scd + scr, cy - bcr, cx + scd + scr, cy + bcr, color=d.CUT)

    def support(cx, cy):
        # draw shape around the router base
        d.circle(cx, cy, bigCircleRadius, color=d.CUT)
        # draw a supporting piece
        supportRadius = unit("30mm")
        x2 = cx + bigCircleRadius + 10 + supportRadius
        y2 = cy - bigCircleRadius + supportRadius
        d.circle(x2, y2, pinRadius, color=d.CUT)
        d.cross(x2, y2, supportRadius, color=d.GUIDE)
        d.circle(x2, y2, supportRadius, color=d.CUT)

    def routerBase(cx, cy, bottom):
        # Hole for the bit
        d.circle(cx, cy, bitDiam / 2, d.CUT)

        # Hole for the cut
        d.circle(cx, cy, cutRadius, d.CUT)

        # Screw holes

        if screws:
            screw_holes = screws.split(";")
            for screw_hole in screw_holes:
                attrs = screw_hole.split(",")
                assert len(attrs) in [3, 4]
                sx = cx + unit(attrs[0])
                sy = cy + unit(attrs[1])
                sr = unit(attrs[2]) / 2
                d.cross(sx, sy, 1, d.MARK)
                if not bottom or len(attrs) == 3:
                    # smaller hole
                    d.circle(sx, sy, sr, d.CUT)
                    if layers == LAYER_SINGLE and len(attrs) == 4:
                        sr = unit(attrs[3]) / 2
                        d.circle(sx, sy, sr, d.MARK)
                elif bottom:
                    if len(attrs) == 4:
                        sr = unit(attrs[3]) / 2
                    d.circle(sx, sy, sr, d.CUT)

        # Screw slides
        if screwSlides:
            attrs = screwSlides.split(':')
            assert len(attrs) in [4, 5]
            angs = attrs[0].split(',')
            rad1 = unit(attrs[1])
            rad2 = unit(attrs[2])
            dbg(rad1)
            diam0 = unit(attrs[3])
            diam1 = unit(attrs[4]) if len(attrs) == 5 else diam0

            def genSlide(angle, rad1, rad2, diam, color):
                x0 = cx + math.cos(angle) * rad1
                y0 = cy + math.sin(angle) * rad1
                x1 = cx + math.cos(angle) * rad2
                y1 = cy + math.sin(angle) * rad2
                d.arc(x0, y0, diam / 2, math.pi / 2, angle, color=color)
                d.arc(x1, y1, diam / 2, math.pi / 2, math.pi + angle, color=color)
                lx0 = x0 + math.cos(angle + math.pi / 2) * diam / 2
                ly0 = y0 + math.sin(angle + math.pi / 2) * diam / 2
                lx1 = x1 + math.cos(angle + math.pi / 2) * diam / 2
                ly1 = y1 + math.sin(angle + math.pi / 2) * diam / 2
                d.line(lx0, ly0, lx1, ly1, color=color)
                rx0 = x0 + math.cos(angle - math.pi / 2) * diam / 2
                ry0 = y0 + math.sin(angle - math.pi / 2) * diam / 2
                rx1 = x1 + math.cos(angle - math.pi / 2) * diam / 2
                ry1 = y1 + math.sin(angle - math.pi / 2) * diam / 2
                d.line(rx0, ry0, rx1, ry1, color=color)

            for angDegs in angs:
                ang = math.radians(float(angDegs))
                if not bottom or len(attrs) == 4:
                    # smaller slide
                    genSlide(ang, rad1, rad2, diam0, color=d.CUT)
                    if layers == LAYER_SINGLE and len(attrs) == 5:
                        # larger slide - mark
                        genSlide(ang, rad1, rad2, diam1, color=d.MARK)
                elif bottom:
                    genSlide(ang, rad1, rad2, diam1, color=d.CUT)

    def glueGuides(cx, cy):
        radius = bigCircleRadius - 5 * pinRadius
        for ang in [60, 210, 285]:
            x = cx + math.cos(math.radians(ang)) * radius
            y = cy + math.sin(math.radians(ang)) * radius
            d.circle(x, y, pinRadius, color=d.CUT)

    # First layer
    routerBase(CX, CY, bottom=False)
    generatePins(CX, CY, bottom=False)
    outline(CX, CY)
    # Second layer, if needed
    CY2 = CY + 2 * bigCircleRadius + 20
    if layers in [LAYER_DOUBLE, LAYER_SUPPORT]:
        routerBase(CX, CY2, bottom=True)
        glueGuides(CX, CY)
        glueGuides(CX, CY2)
        if layers == LAYER_DOUBLE:
            generatePins(CX, CY2, bottom=True)
            outline(CX, CY2)
        else:
            support(CX, CY2)

    print(d.write())



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
