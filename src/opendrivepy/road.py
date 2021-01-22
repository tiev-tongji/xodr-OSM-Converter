from __future__ import division, print_function, absolute_import

from opendrivepy.point import EndPoint


class Road(object):
    def __init__(self, name, length, id, junction, predecessor, successor, plan_view, elevations, lanes):
        self.name = name
        self.length = length
        self.id = id
        self.junction = junction
        self.predecessor = predecessor
        self.successor = successor
        self.type = list()
        self.is_connection = False
        self.plan_view = plan_view
        self.lane_section = lanes.lane_section
        self.start_lway_id = 0
        self.start_rway_id = 0

        self.ln = 0
        self.rn = 0
        self.ldwidth = list()
        self.rdwidth = list()
        self.lswidth = list()
        self.rswidth = list()

        for lane in self.lane_section.left:
            if lane.type == "driving":
                self.ln += 1
                self.ldwidth.append(lane.width.a)
            elif lane.type == "sidewalk":
                self.lswidth.append(lane.width.a)

        for lane in self.lane_section.right:
            if lane.type == "driving":
                self.rn += 1
                self.rdwidth.append(lane.width.a)
            elif lane.type == "sidewalk":
                self.rswidth.append(lane.width.a)

        self.style = plan_view[0].style # style can be 'line', 'arc', 'spiral' or 'mix'
        for view in plan_view[1:]:
            if view.style != self.style and view.length > 1e-2:
                self.style = 'mix'
                break

        self.points = list()
        self.arcrad = 0
        # a road is composed by serval plan views
        # TODO: WHY??
        for view in self.plan_view:
            if view.style == 'arc' and view.length > 1e-2 and view.radius > self.arcrad and view.radius < 100:
                self.arcrad = view.radius
            for point in view.points:
                self.points.append(point)
        # print(self.arcrad)

        self.elevation_profile = elevations

        points_id = 0
        for i in range(len(elevations)-1):
            elevation = elevations[i]
            if elevation.a != 0 or elevation.b != 0 or elevation.c != 0 or elevation.d != 0: # has banking
                while points_id < len(self.points):
                    if self.points[points_id].s >= elevations[i+1].s:
                        break
                    
                    ds = self.points[points_id].s - elevation.s
                    self.points[points_id].z = elevation.a + elevation.b * ds + elevation.c * (ds**2) + elevation.d * (ds**3)
                    points_id += 1



        elevation = elevations[-1]
        if elevation.a != 0 or elevation.b != 0 or elevation.c != 0 or elevation.d != 0: # has banking
            while points_id < len(self.points):                
                ds = self.points[points_id].s - elevation.s
                self.points[points_id].z = elevation.a + elevation.b * ds + elevation.c * (ds**2) + elevation.d * (ds**3)
                points_id += 1


        self.lateral_profile = None

        # Points that represent the road
        # Endpoints between records are duplicated atm
        self.points = list()
        self.generate_points()

        self.start_point = EndPoint
        self.end_point = EndPoint
        self.update_endpoints()

    def generate_points(self):
        for record in self.plan_view:
            self.points.extend(record.points)

    def draw_road(self):
        for record in self.plan_view:
            record.graph()

    # Updates the values of self.startPoint and self.endPoint based on the road array
    def update_endpoints(self):
        if self.plan_view is not None:
            x = self.points[0].x
            y = self.points[0].y
            self.start_point = EndPoint(x, y, self.id, 'start')

            x = self.points[-1].x
            y = self.points[-1].y
            self.end_point = EndPoint(x, y, self.id, 'end')

    # Determines if b
    def in_range(self, other):
        sp = self.start_point.distance(other)
        if self.start_point.distance(other) <= self.length:
            return True

        return False

    # WARNING: This only works so far with a fix width. Simplified for testing purposes
    def get_left_width(self):
        swidth = 0
        dwidth = 0
        n = 0
        for lane in self.lane_section.left:
            if lane.type == "driving":
                dwidth += lane.width.a
                n += 1
            elif lane.type == "sidewalk":
                swidth += lane.width.a

        return swidth, dwidth, n

    def get_right_width(self):
        swidth = 0
        dwidth = 0
        n = 0
        for lane in self.lane_section.right:
            if lane.type == "driving":
                dwidth += lane.width.a
                n += 1
            elif lane.type == "sidewalk":
                swidth += lane.width.a

        return swidth, dwidth, n

class RoadLink(object):
    def __init__(self, element_type, element_id, contact_point):
        self.element_type = element_type
        self.element_id = element_id
        self.contact_point = contact_point
