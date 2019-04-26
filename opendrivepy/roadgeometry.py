from __future__ import division, print_function, absolute_import

import numpy as np
from scipy.special import fresnel
from matplotlib import pyplot as plt
from math import pi, sin, cos, sqrt, fabs, ceil

from opendrivepy.point import Point


class RoadGeometry(object):
    def __init__(self, s, x, y, hdg, length, style):
        self.s = s
        self.x = x
        self.y = y
        self.hdg = hdg
        self.length = length

        self.style = style
        self.points = list()
        self.segments = list()

    def graph(self):
        plt.plot([pt.x for pt in self.points], [pt.y for pt in self.points], self.style)

    def generate_segments(self):
        for i in range(len(self.points)-1):
            self.segments.append(RoadSegment(self.points[i], self.points[i+1]))


class RoadLine(RoadGeometry):
    def __init__(self, s, x, y, hdg, length):
        super(RoadLine, self).__init__(s, x, y, hdg, length, style='b-')
        self.generate_coords()
        self.generate_segments()

    def generate_coords(self):
        for n in (0, self.length):
            x = self.x + (n * cos(self.hdg))
            y = self.y + (n * sin(self.hdg))
            self.points.append(Point(x, y))


class RoadArc(RoadGeometry):
    def __init__(self, s, x, y, hdg, length, curvature):
        super(RoadArc, self).__init__(s, x, y, hdg, length, 'r-')
        self.curvature = curvature
        self.generate_coords(int(ceil(self.length) + 1))
        self.generate_segments()

    def base_arc(self, n):
        radius = fabs(1/self.curvature)
        circumference = radius * pi * 2
        angle = (self.length/circumference) * 2 * pi
        # If curvature < 0, then the arc rotates clockwise
        if self.curvature > 0:
            start_angle = self.hdg - (pi / 2)
            circlex = self.x - (cos(start_angle) * radius)
            circley = self.y - (sin(start_angle) * radius)

            array = list(range(n))
            return radius, circlex, circley, [start_angle + (angle * x / (n-1)) for x in array]
        # Otherwise it is anticlockwise
        else:
            start_angle = self.hdg + (pi / 2)
            circlex = self.x - (cos(start_angle) * radius)
            circley = self.y - (sin(start_angle) * radius)
            array = list(range(n))
            return radius, circlex, circley, [start_angle - (angle * x / (n-1)) for x in array]

    def generate_coords(self, n):
        r, circle_x, circle_y, array = self.base_arc(n)

        for n in array:
            x = circle_x + (r * cos(n))
            y = circle_y + (r * sin(n))
            self.points.append(Point(x, y))


class RoadSpiral(RoadGeometry):
    def __init__(self, s, x, y, hdg, length, curvstart, curvend):
        super(RoadSpiral, self).__init__(s, x, y, hdg, length, 'g-')
        self.curvStart = curvstart
        self.curvEnd = curvend
        self.cDot = (curvend-curvstart)/length
        self.spiralS = curvstart/self.cDot
        self.generate_coords(int(ceil(self.length) + 1))
        self.generate_segments()

    # Approximates the standard Euler spiral at a point length s along the curve
    def odr_spiral(self, s):
        a = 1 / sqrt(fabs(self.cDot))
        a *= sqrt(pi)

        y, x = fresnel(s / a)

        x *= a
        y *= a

        if self.cDot < 0:
            y *= -1

        t = s * s * self.cDot * 0.5
        return x, y, t

    # Approximates a piece of the standard Euler spiral using n points
    # The spiral is adjusted such that it stars along x=0
    def base_spiral(self, n):
        ox, oy, theta = self.odr_spiral(self.spiralS)
        sin_rot = sin(theta)
        cos_rot = cos(theta)
        xcoords = list()
        ycoords = list()
        for i in range(n):
            tx, ty, ttheta = self.odr_spiral((i * self.length / n) + self.spiralS)

            dx = tx - ox
            dy = ty - oy
            xcoords.append(dx * cos_rot + dy * sin_rot)
            ycoords.append(dy * cos_rot - dx * sin_rot)

        return xcoords, ycoords

    def evaluate_spiral(self, n):
        xarr, yarr = self.base_spiral(n)
        sinRot = sin(self.hdg)
        cosRot = cos(self.hdg)
        for i in range(n):
            tmpX = self.x + cosRot * xarr[i] - sinRot * yarr[i]
            tmpY = self.y + cosRot * yarr[i] + sinRot * xarr[i]
            xarr[i] = tmpX
            yarr[i] = tmpY

        return xarr, yarr

    def generate_coords(self, n):
        xarr, yarr = self.evaluate_spiral(n)
        for x, y in zip(xarr, yarr):
            self.points.append(Point(x, y))


class RoadParamPoly3(RoadGeometry):
    def __init__(self, s, x, y, hdg, length, aU, bU, cU, dU, aV, bV, cV, dV):
        super(RoadParamPoly3, self).__init__(s, x, y, hdg, length, 'y-')
        self.aU = aU
        self.bU = bU
        self.cU = cU
        self.dU = dU
        self.aV = aV
        self.bV = bV
        self.cV = cV
        self.dV = dV

    def graph(self):
        x = np.array(range(0, self.length))


class RoadSegment(object):
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        self.l2 = (self.p1.x - self.p2.x)**2 + (self.p1.y - self.p2.y)**2

    def min_distance(self, q):
        if self.l2 == 0:
            return self.p1.distance(q)

        t = ((q.x - self.p1.x) * (self.p2.x - self.p1.x) + (q.y - self.p1.y) * (self.p2.y - self.p1.y)) /self.l2
        t = max(0, min(1, t))

        x = self.p1.x + t * (self.p2.x - self.p1.x)
        y = self.p1.y + t * (self.p2.y - self.p1.y)
        projection = Point(x, y)
        return q.distance(projection)

    def min_point(self, q):
        if self.l2 == 0:
            return self.p1.distance(q)

        t = ((q.x - self.p1.x) * (self.p2.x - self.p1.x) + (q.y - self.p1.y) * (self.p2.y - self.p1.y)) / self.l2
        t = max(0, min(1, t))

        x = self.p1.x + t * (self.p2.x - self.p1.x)
        y = self.p1.y + t * (self.p2.y - self.p1.y)
        projection = Point(x, y)
        return projection
