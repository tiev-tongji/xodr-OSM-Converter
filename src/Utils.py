from math import fabs, sqrt
from geompreds import orient2d, incircle
from opendrivepy.point import Point

def point_distance(pointa, pointb):
    return sqrt((pointa.x - pointb.x) ** 2 + (pointa.y - pointb.y) ** 2)


# def line_cross(line1, line2):
#     x1 = line1[0].x
#     y1 = line1[0].y
#     x2 = line1[1].x
#     y2 = line1[1].y

#     x3 = line2[0].x
#     y3 = line2[0].y
#     x4 = line2[1].x
#     y4 = line2[1].y

#     # slope of L1 doesn't exist
#     if (x2-x1) == 0:
#         k1 = None
#         b1 = 0
#     else:
#         k1 = (y2-y1)*1.0/(x2-x1)
#         b1 = y1*1.0-x1*k1*1.0

#     # slope of L2 doesn't exist
#     if (x4-x3) == 0:
#         k2 = None
#         b2 = 0
#     else:
#         k2 = (y4-y3)*1.0/(x4-x3)
#         b2 = y3*1.0-x3*k2*1.0

#     if k1 == None and k2 == None:
#         x = x1
#         y = (y1 + y1 + y3 + y4) / 4.0
#     if k2 == None:
#         x = x3
#         y = (y1 + y1 + y3 + y4) / 4.0
#     if k1 is not None and k2 is not None:
#         x = (b2-b1)*1.0/(k1-k2)
#         y = k1*x*1.0+b1*1.0
#     return Point(x,y)

def line(p1, p2):
    A = (p1.y - p2.y)
    B = (p2.x - p1.x)
    C = (p1.x*p2.y - p2.x*p1.y)
    return A, B, -C

def intersection(L1, L2):
    D  = L1[0] * L2[1] - L1[1] * L2[0]
    Dx = L1[2] * L2[1] - L1[1] * L2[2]
    Dy = L1[0] * L2[2] - L1[2] * L2[0]
    if D != 0:
        x = Dx / D
        y = Dy / D
        return Point(x,y)
    else:
        return False

def line_cross(line1, line2):
    L1 = line(line1[0], line1[1])
    L2 = line(line2[0], line2[1])

    R = intersection(L1, L2)
    if R:
        return R
    else:
        x1 = line1[0].x
        x2 = line1[1].x
        x3 = line2[0].x
        x4 = line2[1].x

        y1 = line1[0].y
        y2 = line1[1].y
        y3 = line2[0].y
        y4 = line2[1].y
        return Point((x1+x2+x3+x4)/4,(y1+y2+y3+y4)/4)

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