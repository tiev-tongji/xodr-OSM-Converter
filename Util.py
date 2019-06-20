from math import fabs, sqrt
from geompreds import orient2d, incircle
from opendrivepy.point import Point

def point_distance(pointa, pointb):
    return sqrt((pointa.x - pointb.x) ** 2 + (pointa.y - pointb.y) ** 2)


def line_cross(line1, line2):
    x1 = line1[0].x
    y1 = line1[0].y
    x2 = line1[1].x
    y2 = line1[1].y

    x3 = line2[0].x
    y3 = line2[0].y
    x4 = line2[1].x
    y4 = line2[1].y

    k1 = (y2-y1)*1.0/(x2-x1)
    b1 = y1*1.0-x1*k1*1.0

    # slope of L2 doesn't exist
    if (x4-x3) == 0:
        k2 = None
        b2 = 0
    else:
        k2 = (y4-y3)*1.0/(x4-x3)
        b2 = y3*1.0-x3*k2*1.0

    if k2 == None:
        x = x3
    else:
        x = (b2-b1)*1.0/(k1-k2)
    y = k1*x*1.0+b1*1.0
    return Point(x,y)


def orient_node(nodea, nodeb, nodec):
    return orient2d((nodea.x, nodea.y), (nodeb.x, nodeb.y), (nodec.x, nodec.y))


def find_diagonal(nodes):
    # find the diagonal node of node[0]
    if orient_node(nodes[0], nodes[1], nodes[2]) * orient_node(nodes[3], nodes[1], nodes[2]) < 0:
        return 3
    elif orient_node(nodes[0], nodes[1], nodes[3]) * orient_node(nodes[2], nodes[1], nodes[3]) < 0:
        return 2
    else:
        return 1