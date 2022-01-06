class Node(object):
    """docstring for Node"""

    def __init__(self, node_id, x, y, z, max_arcrad=0, color = 'y.',road_id=0,is_mid=False,lane_num=0,lane_seq=0,lane_width=0,heading=0,utmx=0,utmy=0,way_id=0):
        super(Node, self).__init__()
        self.id = node_id
        self.x = x
        self.y = y
        self.z = z
        self.max_arcrad = max_arcrad
        self.color = color

        """add"""
        self.is_mid=is_mid
        self.lane_num=lane_num
        self.lane_seq=lane_seq
        self.heading=heading
        self.road_id=road_id
        self.lane_width=lane_width
        self.utmx=utmx
        self.utmy=utmy
        self.way_id=way_id


class Way(object):
    """docstring for Way"""

    def __init__(self, way_id, nodes_id, width, offset,
                 is_connecting, style, nleft, nright,
                 walkleft, walkright):
        super(Way, self).__init__()
        self.id = way_id
        self.is_connecting = is_connecting

        # self.has_successor = False
        # self.successor_id = None
        # if successor_id is not None:
        #     self.successor_id = successor_id
        #     self.has_successor = True

        self.nodes_id = nodes_id
        self.width = width
        self.offset = offset
        self.style = style
        self.nrightlanes = nright
        self.nleftlanes = nleft
        self.widthrightwalk = walkright
        self.widthleftwalk = walkleft
