from __future__ import division, print_function, absolute_import

from opendrivepy.point import EndPoint


class Road(object):
    def __init__(self, name, length, id, predecessor, successor, points):
        self.name = name
        self.length = length
        self.id = id
        self.predecessor = predecessor
        self.successor = successor
        self.type = list()
        self.is_connection = False

        self.points = points

        self.lateral_profile = None
        # self.lanes = lanes

        # Points that represent the road
        # Endpoints between records are duplicated atm
        self.start_point = EndPoint
        self.end_point = EndPoint
        self.update_endpoints()

    # Updates the values of self.startPoint and self.endPoint based on the road array
    def update_endpoints(self):
        x = self.points[0].x
        y = self.points[0].y
        z = self.points[0].z
        self.start_point = EndPoint(x, y, z, self.id, 'start')

        x = self.points[-1].x
        y = self.points[-1].y
        z = self.points[-1].z
        self.end_point = EndPoint(x, y, z, self.id, 'end')

    # Determines if b
    def in_range(self, other):
        sp = self.start_point.distance(other)
        if self.start_point.distance(other) <= self.length:
            return True

        return False

class RoadLink(object):
    def __init__(self, element_type, element_id, contact_point):
        self.element_type = element_type
        self.element_id = element_id
        self.contact_point = contact_point
