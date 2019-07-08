from __future__ import division, absolute_import, print_function
import xml.etree.ElementTree as ET
from math import fabs, sqrt
import matplotlib.pyplot as plt
from datetime import datetime

from opendrivepy.opendrive import OpenDrive
from opendrivepy.point import Point
from tqdm import tqdm
from pyqtree import Index

from osmtype import *
from Utils import *

# To avoid the conflict between nodes
# Any points that is too close with peer ( < min distance ) are discarded
min_distance = 1
MAX_ARC_RADIUS = 50


class Converter(object):
    """docstring for Converter"""

    def __init__(self, filename, scene_scale):
        super(Converter, self).__init__()

        print("Reading OpenDrive file: " + filename)
        self.opendrive = OpenDrive(filename)
        self.scale, minx, miny, maxx, maxy = self.set_scale(scene_scale)
        # print(self.scale)

        print("Converting...")
        self.node_id = 0
        self.ways = dict()
        self.nodes = list()

        self.spindex = Index(bbox=(minx, miny, maxx, maxy))
        self.convert()
        print("done")

    def set_scale(self, scene_scale):
        # cast the bigger map into a smaller map
        tar_scale = scene_scale  # target boundary is [-tar_scale,tar_scale]
        x = []
        y = []
        length = []

        for road in self.opendrive.roads.values():
            for geometry in road.plan_view:
                x.append(geometry.x)
                y.append(geometry.y)
                length.append(geometry.length)

        maxx = max(x)
        maxy = max(y)
        minx = min(x)
        miny = min(y)
        # scale = max([(maxx - minx), (maxy - miny)]) / tar_scale
        # print(scale)

        # if scale == 0:
        #     scale = max(length) / tar_scale

        return scene_scale, minx, miny, maxx, maxy

    def convert(self):
        # 1. convert all roads into nodes+ways

        with tqdm(total=len(self.opendrive.roads), ascii=True) as pbar:
            for road_id, road in self.opendrive.roads.items():
                pbar.set_description("Processing road_id=%s" % road_id)
                way_nodes_id = list()

                # all points in a road
                for point in road.points:
                    # search for dup
                    near_node_ids = self.spindex.intersect(
                        (point.x, point.y, point.x, point.y))

                    if len(near_node_ids) > 0: # dup exists
                        if not (near_node_ids[0] in way_nodes_id): # not exists in current way_nodes_id
                            # if the new node A is quite close to an existing node B, use B
                            way_nodes_id.append(near_node_ids[0])
                    else:
                        # add a new node
                        self.nodes.append(
                            Node(self.node_id, point.x, point.y, 0))
                        way_nodes_id.append(self.node_id)
                        self.spindex.insert(
                            self.node_id, (point.x-min_distance, point.y-min_distance, point.x+min_distance, point.y+min_distance))
                        self.node_id = self.node_id + 1

                # set the width of ways
                if len(way_nodes_id) > 0:
                    ws_left, wd_left, n_left = road.get_left_width()
                    ws_right, wd_right, n_right = road.get_right_width()
                    width = wd_left + wd_right

                    offset = width/2 - wd_right
                    self.ways[road_id] = Way(
                        road_id, way_nodes_id, width, offset, road.is_connection, road.style, n_left, n_right, ws_left, ws_right)
                pbar.update(1)

        # 2. handle the junctions: merge nodes & switch the end points of roads
        for junction in self.opendrive.junctions.values():
            if len(junction.lane_link) >= 2:
                is_Tshape_junction = False
                is_Xshape_junction = False

                if len(junction.lane_link) == 3:
                    is_Tshape_junction = self.handle_Tshape(junction)

                if len(junction.lane_link) == 4:
                    is_Xshape_junction = True
                    self.handle_Xshape(junction)

                if not is_Tshape_junction and not is_Xshape_junction:
                    self.handle_Nshape(junction)

        # return ways, nodes

    def way_end_to_point(self, node_id, way_id):
        # find the closer end (0/-1) of the way to the node
        distance_to_start = point_distance(
            self.nodes[node_id], self.nodes[self.ways[way_id].nodes_id[0]])
        distance_to_end = point_distance(
            self.nodes[node_id], self.nodes[self.ways[way_id].nodes_id[-1]])

        if distance_to_start < distance_to_end:
            return 0
        else:
            return -1

    def handle_Tshape(self, junction):
        # A T shape junction would be like:
        # ----1---*---2----
        #         |
        #         |
        #         3
        #         4
        #         |
        #         |
        #
        # we need to get the * point
        # so we use four points to interpolate

        is_Tshape_junction = False

        lane_link = junction.lane_link
        line1_nodes = list()
        for connection in junction.connections:

            # 1. add the contact point (1,2) of a T junction
            if self.ways[connection.connecting_road].style == 'line':
                incoming_road = connection.incoming_road
                connecting_road = connection.connecting_road
                contact_point = connection.contact_point

                contact_node_id = self.ways[connecting_road].nodes_id[0 if contact_point == 'start' else -1]
                way_end = self.way_end_to_point(contact_node_id, incoming_road)

                line1_nodes.append(
                    self.nodes[self.ways[incoming_road].nodes_id[way_end]])
                self.ways[incoming_road].nodes_id[way_end] = self.node_id

                # search and delete the incoming road in lane_link we just used
                for i in range(len(lane_link)):
                    if lane_link[i][0] == incoming_road:
                        del lane_link[i]
                        break

        line2_nodes = list()
        if len(line1_nodes) >= 2:
            is_Tshape_junction = True

            # 2. add the contact point (3,4) of a T junction
            for incoming_road, connecting_road, contact_point in lane_link:
                contact_node_id = self.ways[connecting_road].nodes_id[0 if contact_point == 'start' else -1]
                way_end = self.way_end_to_point(contact_node_id, incoming_road)

                line2_nodes.append(
                    self.nodes[self.ways[incoming_road].nodes_id[way_end]])
                self.ways[incoming_road].nodes_id[way_end] = self.node_id
                line2_nodes.append(
                    self.nodes[self.ways[incoming_road].nodes_id[(way_end + 1 if way_end == 0 else way_end - 1)]])

            # calculate the cross point of line(1,2) and line(3,4)
            cross_point = line_cross(line1_nodes, line2_nodes)

            line1_nodes.extend(line2_nodes)
            min_distance_to_center = min(point_distance(
                cross_point, p) for p in line1_nodes)

            self.nodes.append(
                Node(self.node_id, cross_point.x, cross_point.y, 0, min([junction.max_arcrad, min_distance_to_center])))
            self.node_id = self.node_id + 1

        return is_Tshape_junction

    def handle_Xshape(self, junction):

        line_nodes = list()
        for incoming_road, connecting_road, contact_point in junction.lane_link:
            contact_node_id = self.ways[connecting_road].nodes_id[0 if contact_point == 'start' else -1]
            way_end = self.way_end_to_point(contact_node_id, incoming_road)
            line_nodes.append(
                self.nodes[self.ways[incoming_road].nodes_id[way_end]])
            self.ways[incoming_road].nodes_id[way_end] = self.node_id

        diag_node_index = find_diagonal(line_nodes)
        if diag_node_index != 1:  # we fix 0,1 as diagonal pair
            line_nodes[1], line_nodes[diag_node_index] = line_nodes[diag_node_index], line_nodes[1]

        cross_point = line_cross(line_nodes[:2], line_nodes[2:])
        min_distance_to_center = min(point_distance(
            cross_point, p) for p in line_nodes)
        # print(min_distance_to_center, junction.max_arcrad)

        self.nodes.append(
            Node(self.node_id, cross_point.x, cross_point.y, 0, min([junction.max_arcrad, min_distance_to_center])))
        self.node_id = self.node_id + 1

    def handle_Nshape(self, junction):
        
        line1_nodes = list()
        line2_nodes = list()
        last_cross_point = None

        # add the contact point of an incoming road as line1
        incoming_road, connecting_road, contact_point = junction.lane_link[0]
        contact_node_id = self.ways[connecting_road].nodes_id[0 if contact_point == 'start' else -1]
        way_end = self.way_end_to_point(contact_node_id, incoming_road)

        line1_nodes.append(
            self.nodes[self.ways[incoming_road].nodes_id[way_end]])
        self.ways[incoming_road].nodes_id[way_end] = self.node_id
        line1_nodes.append(
            self.nodes[self.ways[incoming_road].nodes_id[(way_end + 1 if way_end == 0 else way_end - 1)]])

        # add the contact point of an incoming road as line2
        for incoming_road, connecting_road, contact_point in junction.lane_link[1:]:
            contact_node_id = self.ways[connecting_road].nodes_id[0 if contact_point == 'start' else -1]
            way_end = self.way_end_to_point(contact_node_id, incoming_road)

            line2_nodes.append(
                self.nodes[self.ways[incoming_road].nodes_id[way_end]])
            self.ways[incoming_road].nodes_id[way_end] = self.node_id
            line2_nodes.append(
                self.nodes[self.ways[incoming_road].nodes_id[(way_end + 1 if way_end == 0 else way_end - 1)]])

            # calculate the cross point of line1 and line2
            cross_point = line_cross(line1_nodes, line2_nodes)
            line1_nodes = line2_nodes

            if last_cross_point is not None:
                if point_distance(last_cross_point, cross_point) > min_distance:
                    self.nodes.append(
                        Node(self.node_id, last_cross_point.x, last_cross_point.y, 0, 5))
                    self.node_id = self.node_id + 1
                    last_cross_point = cross_point
            else:        
                last_cross_point = cross_point

        self.nodes.append(
            Node(self.node_id, cross_point.x, cross_point.y, 0,  5))
        self.node_id = self.node_id + 1


            # min_distance_to_center = min(point_distance(
            #     cross_point, p) for p in line1_nodes)

            # self.nodes.append(
            #     Node(self.node_id, cross_point.x, cross_point.y, min([junction.max_arcrad, min_distance_to_center])))
            # self.node_id = self.node_id + 1

        # sum_x = 0
        # sum_y = 0

        # min_distance_to_center = MAX_ARC_RADIUS
        # for incoming_road, connecting_road, contact_point in junction.lane_link:

        #     contact_node_id = self.ways[connecting_road].nodes_id[0 if contact_point == 'start' else -1]

        #     way_end = self.way_end_to_point(contact_node_id, incoming_road)

        #     sub_node = self.nodes[self.ways[incoming_road].nodes_id[way_end]]
        #     self.ways[incoming_road].nodes_id[way_end] = self.node_id

        #     # to calculate the center point of junctions
        #     sum_x += sub_node.x
        #     sum_y += sub_node.y

        # self.nodes.append(Node(self.node_id, sum_x / len(junction.lane_link),
        #                        sum_y / len(junction.lane_link),  min([junction.max_arcrad, min_distance_to_center])))
        # self.node_id = self.node_id + 1

    def generate_osm(self, filename, debug = False):
        if debug:
            for node in self.nodes:
                plt.plot(node.x, node.y, node.color)
            plt.show()

        osm_attrib = {'version': "0.6", 'generator': "xodr_OSM_converter", 'copyright': "Simon",
                      'attribution': "Simon", 'license': "GNU or whatever"}
        osm_root = ET.Element('osm', osm_attrib)

        bounds_attrib = {'minlat': '0', 'minlon': '0',
                         'maxlat': '1', 'maxlon': '1'}
        ET.SubElement(osm_root, 'bounds', bounds_attrib)

        # add all nodes into osm
        for node in self.nodes:
            node_attrib = {'id': str(node.id), 'visible': 'true', 'version': '1', 'changeset': '1', 'timestamp': datetime.utcnow().strftime(
                '%Y-%m-%dT%H:%M:%SZ'), 'user': 'simon', 'uid': '1', 'lat': str(node.x / self.scale), 'lon': str(node.y / self.scale), 'ele':'2'}
            node_root = ET.SubElement(osm_root, 'node', node_attrib)

            ET.SubElement(node_root, 'tag', {'k': "type", 'v': 'Crossing'})
            # ET.SubElement(node_root, 'tag', {'k': "y", 'v': '2'})
            ET.SubElement(node_root, 'tag', {
                          'k': "minArcRadius", 'v': str(node.max_arcrad)})

        for way_key, way_value in self.ways.items():
            if way_value.is_connecting:  # ignore all connecting roads
                continue

            way_attrib = {'id': str(way_key), 'version': '1', 'changeset': '1',
                          'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'), 'user': 'simon', 'uid': '1'}
            way_root = ET.SubElement(osm_root, 'way', way_attrib)

            # add all nodes of a road
            for way_node in way_value.nodes_id:
                ET.SubElement(way_root, 'nd', {'ref': str(way_node)})

            # ET.SubElement(way_root, 'tag', {'k': "highway", 'v':'tertiary'})
            ET.SubElement(way_root, 'tag', {
                          'k': "name", 'v': 'road'+str(way_value.id)})
            ET.SubElement(way_root, 'tag', {
                          'k': "streetWidth", 'v': str(way_value.width)})
            ET.SubElement(way_root, 'tag', {
                          'k': "streetOffset", 'v': str(way_value.offset)})
            ET.SubElement(way_root, 'tag', {
                          'k': "sidewalkWidthLeft", 'v': str(way_value.widthleftwalk)})
            ET.SubElement(way_root, 'tag', {
                          'k': "sidewalkWidthRight", 'v': str(way_value.widthrightwalk)})
            ET.SubElement(way_root, 'tag', {
                          'k': "NbrOfRightLanes", 'v': str(way_value.nrightlanes)})

            ET.SubElement(way_root, 'tag', {
                          'k': "nLanesTotal", 'v': str(way_value.nrightlanes + way_value.nleftlanes)})
            if way_value.nrightlanes == 0 or way_value.nleftlanes == 0:
                ET.SubElement(way_root, 'tag', {
                    'k': "Centerline", 'v': "none"})

        tree = ET.ElementTree(osm_root)
        tree.write(filename)


Converter('./xodr/Town05.xodr', 100000).generate_osm('./osm/Town05.osm', False)
