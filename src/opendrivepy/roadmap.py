from __future__ import division, print_function, absolute_import


class RoadMap(object):
    def __init__(self, roads):
        self.roads = roads

    # Finds the closest point on the roads to the given point
    def closest_point(self, q):
        min_dist = 100
        min_segment = None
        road_left = 0
        road_right = 0

        roads = self.roads
        for road in roads.values():
            # if road.in_range(q) is False:
            #     continue
            left = road.get_left_width(0)
            right = road.get_right_width(0)
            for segment in road.segments:
                if segment.min_distance(q) < min_dist and self.in_range(segment, q, left, right, segment.min_distance(q)):
                    min_segment = segment
                    min_dist = segment.min_distance(q)
                    road_left = left
                    road_right = right
                    print(road.id)

        return min_segment, road_right, road_left

    # Returns the orientation of the point with respect to the line formed by s and e
    # 1 if the point is left of the line looking at e from s, -1 on the right and 0 on the line
    def side(self, s, e, q):
        dotperp = ((e.x - s.x) * (q.y - s.y)) - ((e.y - s.y) * (q.x - s.x))
        return bool(dotperp > 0) - bool(dotperp < 0)

    def in_range(self, segment, q, left, right, dist):
        side = self.side(segment.p1, segment.p2, q)
        if side == 0:  # on the line
            return True
        elif side == 1:  # left
            return dist <= left
        else:  # right
            return dist <= right

    def is_on_road(self, q):
        min_segment, right, left = self.closest_point(q)
        if min_segment is not None:
            return True
        return False

