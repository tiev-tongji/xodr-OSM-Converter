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

class RoadElevation(object):
    def __init__(self, s, a, b, c, d):
        self.s = s
        self.a = a
        self.b = b
        self.c = c
        self.d = d

class RoadLine(RoadGeometry):
    def __init__(self, s, x, y, hdg, length):
        super(RoadLine, self).__init__(s, x, y, hdg, length, style='line')
        self.generate_coords()

    def generate_coords(self):
        for n in (0, self.length):
            x = self.x + (n * cos(self.hdg))
            y = self.y + (n * sin(self.hdg))
            self.points.append(Point(x, y, n))


class RoadArc(RoadGeometry):
    def __init__(self, s, x, y, hdg, length, curvature):
        super(RoadArc, self).__init__(s, x, y, hdg, length, 'arc')
        self.curvature = curvature
        self.radius = fabs(1/self.curvature)
        self.generate_coords(int(ceil(self.length) + 1))

    def base_arc(self, n):
        radius = self.radius
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
            self.points.append(Point(x, y, n))


class RoadSpiral(RoadGeometry):
    def __init__(self, s, x, y, hdg, length, curvstart, curvend):
        super(RoadSpiral, self).__init__(s, x, y, hdg, length, 'spiral')
        self.curvStart = curvstart
        self.curvEnd = curvend
        self.cDot = (curvend-curvstart)/length
        self.spiralS = curvstart/self.cDot
        self.generate_coords(int(ceil(self.length) + 1))

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
        for i in range(n):
            self.points.append(Point(xarr[i], yarr[i], i))
