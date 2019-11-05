class Node(object):
    """docstring for Node"""

    def __init__(self, node_id, x, y, z, max_arcrad=0, color = 'y.'):
        super(Node, self).__init__()
        self.id = node_id
        self.x = x
        self.y = y
        self.z = z
        self.max_arcrad = max_arcrad
        self.color = color


class Way(object):
    """docstring for Way"""

    def __init__(self, way_id, nodes_id):
        super(Way, self).__init__()
        self.id = way_id

        # self.has_successor = False
        # self.successor_id = None
        # if successor_id is not None:
        #     self.successor_id = successor_id
        #     self.has_successor = True

        self.nodes_id = nodes_id

