import math
import sys
import xml.etree.ElementTree as ET


def dbg(s):
    print(str(s), file=sys.stderr)

def err(s):
    print(str(s), file=sys.stderr)
    sys.exit(0)

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
        self.width = 0.3
        self.fill = self.NONE
        self.content = ""
        self.bounds = [0, 0, 0, 0]

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
            s += f' stroke-width="{width}"'
        return s

    def line(self, x0, y0, x1, y1, color=None, extra=""):
        self.inc_bounds(x0, y0)
        self.inc_bounds(x1, y1)
        self.content += f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y1}" {self.stroke(color)} {extra}/>'

    def cross(self, x, y, size, color=None):
        self.line(x - size, y, x + size, y, color)
        self.line(x, y - size, x, y + size, color)

    def circle(self, x, y, radius, color=None):
        self.inc_bounds(x - radius, y - radius)
        self.inc_bounds(x + radius, y + radius)
        self.content += f'<circle cx="{x}" cy="{y}" r="{radius}" {self.stroke(color)}/>'

    def text(self, x, y, text, color=None, fs=5, anchor="middle", extra=""):
        color = color or self.color
        self.content += f'<text style="font-family:monospace" fill="{color}" x="{x}" y="{y}" font-size="{fs}" text-anchor="{anchor}" {extra}>{text}</text>'

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
            <path d=" M {x0} {y0} A {radius} {radius} 0 {largeArc} 1 {x1} {y1}" {stroke}/>
        """
        self.inc_bounds(cx - radius, cy - radius)
        self.inc_bounds(cx + radius, cy + radius)

    def toSVG(self):
        minx = self.bounds[0]
        miny = self.bounds[1]
        maxx = math.ceil(self.bounds[2] + self.margin)
        maxy = math.ceil(self.bounds[3] + self.margin)
        assert minx == 0 and miny == 0
        width = maxx
        height = maxy
        s = f'<svg  version="1.1" xmlns="http://www.w3.org/2000/svg" width="{width}mm" height="{height}mm" viewBox="0 0 {maxx} {maxy}">'
        s += self.content
        s += f'</svg>'

        try:
            elem = ET.fromstring(s)
            ET.indent(elem, space="  ", level=0)
            s = ET.tostring(elem, encoding='utf8', method='xml').decode()
            s = s.replace('ns0:', '').replace(':ns0', '')
            return s
        except ET.ParseError as e:
            err(str(e) + f"\n...{s[e.position[1] - 30 : e.position[1] + 30]}...")


