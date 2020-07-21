from __future__ import division, print_function, absolute_import


class Lanes(object):
    def __init__(self, lane_section):
        self.lane_offset = None
        self.lane_section = lane_section


class LaneSection(object):
    def __init__(self, left, center, right):
        self.left = left
        self.right = right
        self.center = center


class Lane(object):
    def __init__(self, id, type, level, predecessor, successor, width):
        # Attributes
        self.id = id
        self.type = type
        self.level = level

        # Elements
        self.predecessor = predecessor
        self.successor = successor
        self.width = width
        self.border = list()
        self.road_mark = list()

        self.material = list()
        self.visibility = list()
        self.speed = list()
        self.access = list()
        self.height = list()


class LaneLink(object):
    def __init__(self, id):
        self.id = id


class LaneWidth(object):
    def __init__(self, s_offset, a, b, c, d):
        self.s_offset = s_offset
        self.a = a
        self.b = b
        self.c = c
        self.d = d
