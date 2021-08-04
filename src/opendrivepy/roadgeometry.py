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

    '''
    y
      /
     /  hdg
    /)_____  x

    '''
    def generate_coords(self):
        for n in range(0, int(ceil(self.length) + 1)):
            x = self.x + (n * cos(self.hdg))
            y = self.y + (n * sin(self.hdg))
            self.points.append(Point(x, y, self.s + n, self.hdg))

class RoadArc(RoadGeometry):
    def __init__(self, s, x, y, hdg, length, curvature):
        super(RoadArc, self).__init__(s, x, y, hdg, length, 'arc')
        self.curvature = curvature
        self.radius = fabs(1/self.curvature)
        self.generate_coords(int(ceil(self.length) + 1))

    def base_arc(self, n):
        radius = self.radius
        circumference = radius * pi * 2 # 2 pi r
        angle = self.length / radius    # absolutely positive
        # If curvature > 0, then the arc rotates anticlockwise
        if self.curvature > 0:
            # the centre of a circle
            start_angle = self.hdg + (pi / 2)   # from x to centre of circle
            circlex = self.x + (cos(start_angle) * radius)
            circley = self.y + (sin(start_angle) * radius)

            array = list(range(n))  # from 0 to n-1
            
            return radius, circlex, circley, [start_angle - pi + (angle * x / (n-1)) for x in array], array
            
        # Otherwise it is clockwise
        else:
            start_angle = self.hdg - (pi / 2)
            circlex = self.x + (cos(start_angle) * radius)
            circley = self.y + (sin(start_angle) * radius)
            array = list(range(n))
            return radius, circlex, circley, [start_angle + pi - (angle * x / (n-1)) for x in array], array

    def generate_coords(self, n):
        r, circle_x, circle_y, angles, array = self.base_arc(n)

        for n, s in zip(angles, array):
            x = circle_x + (r * cos(n))
            y = circle_y + (r * sin(n))
            
            if self.curvature > 0:
                self.points.append(Point(x, y, self.s + s, n + pi / 2))
            else:
                self.points.append(Point(x, y, self.s + s, n - pi / 2))
        
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
            tx, ty, ttheta = self.odr_spiral((i * self.length / n) + self.spiralS+pi/180)
            
            dx = tx - ox
            dy = ty - oy
            xcoords.append(dx * cos_rot + dy * sin_rot)
            ycoords.append(dy * cos_rot - dx * sin_rot)

        return xcoords, ycoords

    def evaluate_spiral(self, n):
        xarr, yarr = self.base_spiral(n)
        sinRot = sin(self.hdg)
        cosRot = cos(self.hdg)
        for i in range(2*n):
            tmpX = self.x + cosRot * xarr[i] - sinRot * yarr[i]
            tmpY = self.y + cosRot * yarr[i] + sinRot * xarr[i]
            xarr[i] = tmpX
            yarr[i] = tmpY

        return xarr, yarr

    def generate_coords(self, n):
        xarr, yarr = self.evaluate_spiral(n)
        angle=0
        # angle_arr.append(0)
        for i in range(0,2*n,2):
            # if i<n-1:
            #     angle=np.arctan2(yarr[i+1]-yarr[i-1], xarr[i+1]-xarr[i-1])
            angle=np.arctan2(yarr[i+1]-yarr[i],(xarr[i+1]-xarr[i]))
            # if self.cDot < 0:
            #       angle=angle+pi
            self.points.append(Point(xarr[i], yarr[i], self.s+i/2,angle))
            # angle_arr.append(angle)
        # angle_arr[0]=angle_arr[1]
        # for i in range(n):
        #     self.points.append(Point(xarr[i*2], yarr[i*2], i,angle_arr[i]))
