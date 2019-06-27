class Node(object):
    """docstring for Node"""

    def __init__(self, node_id, x, y, max_arcrad=0):
        super(Node, self).__init__()
        self.id = node_id
        self.x = x
        self.y = y
        self.max_arcrad = max_arcrad


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
