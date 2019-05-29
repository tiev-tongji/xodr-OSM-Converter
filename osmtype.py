class Node(object):
    """docstring for Node"""

    def __init__(self, node_id, lat, lon, visible=True):
        super(Node, self).__init__()
        self.id = node_id
        self.lat = lat
        self.lon = lon
        self.visible = 'true' if visible else 'false'


class Way(object):
    """docstring for Way"""

    def __init__(self, way_id,nodes_id, width,offset, successor_id = None):
        super(Way, self).__init__()
        self.id = way_id
        
        self.has_successor = False
        self.successor_id = None
        if successor_id is not None:
            self.successor_id = successor_id
            self.has_successor = True

        self.nodes_id = nodes_id
        self.width = width
        self.offset = offset

