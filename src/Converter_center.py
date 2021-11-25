from __future__ import division, absolute_import, print_function
import xml.etree.ElementTree as ET
from math import fabs, sqrt, sin, cos, pi
import matplotlib.pyplot as plt
from datetime import datetime

from opendrivepy.opendrive import OpenDrive
from opendrivepy.point import Point
from tqdm import tqdm
from pyqtree import Index

from OSMtype import *
from Utils import *
import argparse


# To avoid the conflict between nodes
# Any points that is too close with peer ( < min distance ) are discarded
MAX_ARC_RADIUS = 50


class Converter(object):
    """docstring for Converter"""

    def __init__(self, filename, scene_scale, min_distance):
        super(Converter, self).__init__()

        print("Reading OpenDrive file: " + filename)
        self.opendrive = OpenDrive(filename)
        self.scale, minx, miny, maxx, maxy = self.set_scale(scene_scale)
        self.min_distance = min_distance
        # print(self.scale)

        print("Converting...")
        self.node_id = 0
        self.ways = dict()
        self.nodes = list()

        self.spindex = Index(bbox=(minx, miny, maxx, maxy))
        self.convert()

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
        way_id = 0
        with tqdm(total=len(self.opendrive.roads), ascii=True) as pbar:
            for road_id, road in self.opendrive.roads.items():
                pbar.set_description("Processing road_id=%s" % road_id)
                way_nodes_id = list()

                # all points in a road
                for point in road.points:
                    new_node_id = self.add_node(point.x, point.y, point.z)
                    # print(new_node_id)
                    if not (new_node_id in way_nodes_id): # not exists in current way_nodes_id
                        way_nodes_id.append(new_node_id)                    

                # set the width of ways
                if len(way_nodes_id) > 0:
                    ws_left, wd_left, n_left = 0,0,0
                    ws_right, wd_right, n_right = 0,0,0
                    width = wd_left + wd_right

                    offset = width/2 - wd_right
                    self.ways[road_id] = Way(
                        road_id, way_nodes_id, width, offset, road.is_connection, road.style, n_left, n_right, ws_left, ws_right)
                pbar.update(1)


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

        roadcnt = 0
        while (self.handle_Tshape_singleway(junction, 'l', roadcnt)):
            is_Tshape_junction = True
            roadcnt += 1

        roadcnt = 0
        while (self.handle_Tshape_singleway(junction, 'r', roadcnt)):
            is_Tshape_junction = True
            roadcnt += 1

        return is_Tshape_junction

    def handle_Tshape_singleway(self, junction, side, roadcnt):
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
        ret = 0

        lane_link = junction.lane_link
        line1_nodes = list()
        incomings = list()
        ends = list()

        for connection in junction.connections:
            contact_point = connection.contact_point
            incoming_road = connection.incoming_road
            connecting_road = connection.connecting_road
            

            # 1. add the contact point (1,2) of a T junction
            if self.ways[self.opendrive.roads[connecting_road].start_lway_id].style == 'line':
                inn = self.opendrive.roads[incoming_road].ln if side=='l' else self.opendrive.roads[incoming_road].rn
                con = self.opendrive.roads[connecting_road].ln if side=='l' else self.opendrive.roads[connecting_road].rn
                min = inn if inn < con else con
                if (roadcnt >= min):
                    continue
                ret += 1
                connecting_way = self.opendrive.roads[connecting_road].start_lway_id + roadcnt if side=='l' else self.opendrive.roads[connecting_road].start_rway_id + roadcnt
                incoming_way = self.opendrive.roads[incoming_road].start_lway_id + roadcnt if side=='l' else self.opendrive.roads[incoming_road].start_rway_id + roadcnt
                contact_node_id = self.ways[connecting_way].nodes_id[0 if contact_point == 'start' else -1]
                way_end = self.way_end_to_point(contact_node_id, incoming_way)
                line1_nodes.append(
                    self.nodes[self.ways[incoming_way].nodes_id[way_end]])
                    
                incomings.append(incoming_way)
                ends.append(way_end)
                
                # search and delete the incoming road in lane_link we just used
                for i in range(len(lane_link)):
                    if lane_link[i][0] == incoming_road:
                        del lane_link[i]
                        break

        if (ret <= 0):
            return ret
        line2_nodes = list()
        if len(line1_nodes) >= 2:
            is_Tshape_junction = True

            # 2. add the contact point (3,4) of a T junction
            for incoming_road, connecting_road, contact_point in lane_link:
                
                connecting_way = self.opendrive.roads[connecting_road].start_lway_id + roadcnt if side=='l' else self.opendrive.roads[connecting_road].start_rway_id + roadcnt
                incoming_way = self.opendrive.roads[incoming_road].start_lway_id + roadcnt if side=='l' else self.opendrive.roads[incoming_road].start_rway_id + roadcnt
                contact_node_id = self.ways[connecting_way].nodes_id[0 if contact_point == 'start' else -1]
                way_end = self.way_end_to_point(contact_node_id, incoming_way)

                line2_nodes.append(
                    self.nodes[self.ways[incoming_way].nodes_id[way_end]])
                line2_nodes.append(
                    self.nodes[self.ways[incoming_way].nodes_id[(way_end + 1 if way_end == 0 else way_end - 1)]])
                incomings.append(incoming_way)
                ends.append(way_end)

            # calculate the cross point of line(1,2) and line(3,4)
            cross_point = line_cross(line1_nodes, line2_nodes)
            cross_point.z = (line1_nodes[0].z + line1_nodes[1].z + line2_nodes[0].z + line2_nodes[1].z) /4

            line1_nodes.extend(line2_nodes)
            self.min_distance_to_center = min(point_distance(
                cross_point, p) for p in line1_nodes)
        
            new_node_id = self.add_node(cross_point.x, cross_point.y, cross_point.z, min([junction.max_arcrad, self.min_distance_to_center]))
            
            for incoming_way, way_end in zip(incomings, ends):
                self.ways[incoming_way].nodes_id[way_end] = new_node_id

        return is_Tshape_junction


    def handle_Xshape(self, junction):

        roadcnt = 0
        while (self.handle_Xshape_singleway(junction, 'l', roadcnt)):
            roadcnt += 1

        roadcnt = 0
        while (self.handle_Xshape_singleway(junction, 'r', roadcnt)):
            roadcnt += 1

    
    def handle_Xshape_singleway(self, junction, side, roadcnt):

        line_nodes = list()
        incomings = list()
        ends = list()
        ret = 0
        for incoming_road, connecting_road, contact_point in junction.lane_link:
            inn = self.opendrive.roads[incoming_road].ln if side=='l' else self.opendrive.roads[incoming_road].rn
            con = self.opendrive.roads[connecting_road].ln if side=='l' else self.opendrive.roads[connecting_road].rn
            min = inn if inn < con else con
            if (roadcnt >= min):
                continue

            ret += 1
            connecting_way = self.opendrive.roads[connecting_road].start_lway_id + roadcnt if side=='l' else self.opendrive.roads[connecting_road].start_rway_id + roadcnt
            incoming_way = self.opendrive.roads[incoming_road].start_lway_id + roadcnt if side=='l' else self.opendrive.roads[incoming_road].start_rway_id + roadcnt
            contact_node_id = self.ways[connecting_way].nodes_id[0 if contact_point == 'start' else -1]
            way_end = self.way_end_to_point(contact_node_id, incoming_way)
            line_nodes.append(
                self.nodes[self.ways[incoming_way].nodes_id[way_end]])
            incomings.append(incoming_way)
            ends.append(way_end)
            # self.ways[incoming_road].nodes_id[way_end] = self.node_id

        if (ret <= 3):
            return 0
        diag_node_index = find_diagonal(line_nodes)
        if diag_node_index != 1:  # we fix 0,1 as diagonal pair
            line_nodes[1], line_nodes[diag_node_index] = line_nodes[diag_node_index], line_nodes[1]

        cross_point = line_cross(line_nodes[:2], line_nodes[2:])
        cross_point.z = (line_nodes[0].z + line_nodes[1].z + line_nodes[2].z + line_nodes[3].z) /4

        self.min_distance_to_center = min(point_distance(
            cross_point, p) for p in line_nodes)
        # print(self.min_distance_to_center, junction.max_arcrad)

        new_node_id = self.add_node(cross_point.x, cross_point.y, cross_point.z, min([junction.max_arcrad, self.min_distance_to_center]))
        
        for incoming_way, way_end in zip(incomings, ends):
            self.ways[incoming_way].nodes_id[way_end] = new_node_id

        return ret

    def handle_Nshape(self, junction):
        roadcnt = 0
        while (self.handle_Nshape_singleway(junction, 'l', roadcnt)):
            roadcnt += 1

        roadcnt = 0
        while (self.handle_Nshape_singleway(junction, 'r', roadcnt)):
            roadcnt += 1

    
    def handle_Nshape_singleway(self, junction, side, roadcnt):
        
        line1_nodes = list()
        line2_nodes = list()
        ret = 0

        last_node_id = None

        # add the contact point of an incoming road as line1
        incoming_road, connecting_road, contact_point = junction.lane_link[0]
        inn = self.opendrive.roads[incoming_road].ln if side=='l' else self.opendrive.roads[incoming_road].rn
        con = self.opendrive.roads[connecting_road].ln if side=='l' else self.opendrive.roads[connecting_road].rn
        min = inn if inn < con else con
        if (roadcnt >= min):
            return 0
        
        ret += 1
        connecting_way = self.opendrive.roads[connecting_road].start_lway_id + roadcnt if side=='l' else self.opendrive.roads[connecting_road].start_rway_id + roadcnt
        incoming_way = self.opendrive.roads[incoming_road].start_lway_id + roadcnt if side=='l' else self.opendrive.roads[incoming_road].start_rway_id + roadcnt
        
        contact_node_id = self.ways[connecting_way].nodes_id[0 if contact_point == 'start' else -1]
        way_end = self.way_end_to_point(contact_node_id, incoming_way)

        line1_nodes.append(
            self.nodes[self.ways[incoming_way].nodes_id[way_end]])
        line1_nodes.append(
            self.nodes[self.ways[incoming_way].nodes_id[(way_end + 1 if way_end == 0 else way_end - 1)]])
        # self.ways[incoming_road].nodes_id[way_end] = self.node_id
        first_incoming = incoming_way
        first_end = way_end


        # add the contact point of an incoming road as line2
        for incoming_road, connecting_road, contact_point in junction.lane_link[1:]:
            inn = self.opendrive.roads[incoming_road].ln if side=='l' else self.opendrive.roads[incoming_road].rn
            con = self.opendrive.roads[connecting_road].ln if side=='l' else self.opendrive.roads[connecting_road].rn
            min = inn if inn < con else con
            if (roadcnt >= min):
                continue
            ret += 1
            connecting_way = self.opendrive.roads[connecting_road].start_lway_id + roadcnt if side=='l' else self.opendrive.roads[connecting_road].start_rway_id + roadcnt
            incoming_way = self.opendrive.roads[incoming_road].start_lway_id + roadcnt if side=='l' else self.opendrive.roads[incoming_road].start_rway_id + roadcnt
            contact_node_id = self.ways[connecting_way].nodes_id[0 if contact_point == 'start' else -1]
            way_end = self.way_end_to_point(contact_node_id, incoming_way)

            line2_nodes.append(
                self.nodes[self.ways[incoming_way].nodes_id[way_end]])
            
            line2_nodes.append(
                self.nodes[self.ways[incoming_way].nodes_id[(way_end + 1 if way_end == 0 else way_end - 1)]])

            # calculate the cross point of line1 and line2
            cross_point = line_cross(line1_nodes, line2_nodes)
            line1_nodes = line2_nodes
            line2_nodes = []
            # print(self.node_id)

            if last_node_id is not None:
                if point_distance(self.nodes[last_node_id], cross_point) > self.min_distance * 10:
                    # connect incoming road to the new cross point
                    # and insert new cross point into last road
                    new_node_id = self.add_node(cross_point.x, cross_point.y, 0, 5)
                    self.ways[incoming_way].nodes_id[way_end] = new_node_id
                    last_node_id = new_node_id

                    self.insert_node(last_incoming, new_node_id, last_end )
                    
                else: # connect incoming road to last cross point
                    self.ways[incoming_way].nodes_id[way_end] = last_node_id

            else:
                new_node_id = self.add_node(cross_point.x, cross_point.y, 0, 5)
                self.ways[incoming_way].nodes_id[way_end] = new_node_id
                self.ways[first_incoming].nodes_id[first_end] = new_node_id
                last_node_id = new_node_id

            last_incoming = incoming_way
            last_end = way_end

        return ret



    def add_node(self, x, y, z, arc=0):
        # search for dup
        near_node_ids = self.spindex.intersect((x, y, x, y))

        if len(near_node_ids) > 0: # dup exists
            # if the new node A is quite close to an existing node B, use B
            return near_node_ids[0]
        else:
            # add a new node
            self.nodes.append(Node(self.node_id, x, y, z, arc))
            self.spindex.insert(
                self.node_id, (x-self.min_distance, y-self.min_distance, x+self.min_distance, y+self.min_distance))
            self.node_id = self.node_id + 1
            return self.node_id - 1

    def insert_node(self, way_id, node_id, way_end):
        new_node = self.nodes[node_id]
        way_nodes_id = self.ways[way_id].nodes_id
        found = False
        for i in range(len(way_nodes_id)-1):
            node = self.nodes[way_nodes_id[i]]
            next_node = self.nodes[way_nodes_id[i+1]]
            if min(node.x , next_node.x) <= new_node.x <= max(node.x , next_node.x) and min(node.y , next_node.y) <= new_node.y <= max(node.y , next_node.y):
                if (new_node.x - node.x) * (next_node.y - node.y) == (next_node.x - node.x) * (new_node.y - node.y):
                    self.ways[way_id].nodes_id.insert(i, node_id)
                    found = True
                    break
        if not found:
            if way_end == 0:   
                self.ways[way_id].nodes_id.insert(0, node_id)
            else:
                self.ways[way_id].nodes_id.append(node_id)

    def generate_osm(self, filename, debug = False):
        # plt.axis('scaled')
        wgs84_to_utm =Proj(proj='utm',zone=50,ellps='WGS84')
        base_utmx,base_utmy=wgs84_to_utm(self.opendrive.lon,self.opendrive.lat)
        if 0:
           
           
            node_list=list()
            # fig,ax=plt.subplots()

            
            list_x=list()
            list_y=list()
            for id in self.ways[95].nodes_id:
                node=self.nodes[id]
                if id!=node.id:
                    print("not equal")
                # if id not in id_list:
                #     continue
                list_x.append(node.x)
                list_y.append(node.y)
                node_list.append(node.id)
                if id in self.ways[86].nodes_id:
                    print("id=",id)
            plt.plot(list_x, list_y,"o")
            # plt.axis('scaled')
            # plt.show()
                # plt.show()
            # list_x=list()
            # list_y=list()
            # for id in self.ways[90].nodes_id:
            #     node=self.nodes[id]
            #     if id!=node.id:
            #         print("not equal")
                
            #     list_x.append(node.x)
            #     list_y.append(node.y)
            #     node_list.append(node.id)
            # plt.plot(list_x, list_y,"-o",color="red")
            list_x=list()
            list_y=list()
            for id in self.ways[86].nodes_id:
                node=self.nodes[id]
                if id!=node.id:
                    print("not equal")
                list_x.append(node.x)
                list_y.append(node.y)
                node_list.append(node.id)
            plt.plot(list_x, list_y,"-o")
            
            # ax.scatter(list_x,list_y)
            # for i in range(len(list_x)):
            #     ax.annotate(str(node_list[i])+"+"+str(i),(list_x[i],list_y[i]))
            plt.axis('scaled')
            
            plt.show()

        osm_attrib = {'version': "0.6", 'generator': "xodr_OSM_converter", 'copyright': "Simon",
                      'attribution': "Simon", 'license': "GNU or whatever"}
        osm_root = ET.Element('osm', osm_attrib)

        bounds_attrib = {'minlat': '0', 'minlon': '0',
                         'maxlat': '1', 'maxlon': '1'}
        ET.SubElement(osm_root, 'bounds', bounds_attrib)

        # add all nodes into osm
        for node in self.nodes:
            node_x,node_y= wgs84_to_utm(base_utmx+node.x,base_utmy+node.y,inverse=True)
            node_attrib = {'id': str(node.id+1), 'visible': 'true', 'version': '1', 'changeset': '1', 'timestamp': datetime.utcnow().strftime(
                '%Y-%m-%dT%H:%M:%SZ'), 'user': 'simon', 'uid': '1', 'lon': str(node_x), 'lat': str(node_y), 'ele':'2'}
            node_root = ET.SubElement(osm_root, 'node', node_attrib)

            ET.SubElement(node_root, 'tag', {'k': "type", 'v': 'Smart'})
            ET.SubElement(node_root, 'tag', {'k': "height", 'v': str(node.z)})
            ET.SubElement(node_root, 'tag', {
                          'k': "minArcRadius", 'v': str(node.max_arcrad)})

        for index, way_id in enumerate(self.ways):
            # if way_id!=95 or way_id!=86:
            #     continue
            way_value = self.ways[way_id]
            # if way_value.is_connecting:  # ignore all connecting roads
            #     continue

            way_attrib = {'id': str(index+1), 'version': '1', 'changeset': '1',
                          'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'), 'user': 'simon', 'uid': '1'}
            way_root = ET.SubElement(osm_root, 'way', way_attrib)

            # add all nodes of a road
            for way_node in way_value.nodes_id:
                ET.SubElement(way_root, 'nd', {'ref': str(way_node+1)})

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


RESOURCE_PATH = "../resource/"

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A random road generator')
    parser.add_argument('--debug', type=bool, default=True, help='Is using debug mode')
    parser.add_argument('--input_file', type=str, default='example.xodr', help='Input OpenDRIVE file name')
    parser.add_argument('--scale', type=int, default=10000, help='Scale of xodr file (in meter)')
    parser.add_argument('--precise', type=int, default=0.1, help='Precision of OSM file (in meter)')
    parser.add_argument('--output_file', type=str, default='example.osm', help='Output OSM file name')
    args = parser.parse_args()
    print(args)

    print('Start converting file...')

    converter = Converter(RESOURCE_PATH + args.input_file, args.scale, args.precise)
    converter.generate_osm(RESOURCE_PATH + args.output_file, args.debug)

    print('All done')
