from __future__ import division, print_function, absolute_import


class Junction(object):
    def __init__(self, name, id):
        self.name = name
        self.id = id
        self.connections = list()
        self.priorities = list()
        self.controllers = list()
        
        self.lane_link = list()
        self.added_link = list() # to avoid duplicate

    def add_connection(self, new_connection):
        self.connections.append(new_connection)
        if new_connection.incoming_road not in self.added_link:
            self.lane_link.append([new_connection.incoming_road,new_connection.connecting_road,new_connection.contact_point])
            self.added_link.append(new_connection.incoming_road)


class Connection(object):
    def __init__(self, id, incoming_road, connecting_road, contact_point):
        self.id = id
        self.incoming_road = incoming_road
        self.connecting_road = connecting_road
        self.contact_point = contact_point

# TODO Add Priorities, JunctionGroups and LaneLinks

