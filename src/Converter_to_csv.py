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
import csv
from pyproj import Proj


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
                road.start_lway_id = way_id
                pbar.set_description("Processing road_id=%s" % road_id)
                offset = 0
                next_lane=None
                for lane_i,lane_section in enumerate(road.lane_section_list):
                    offset = 0
                    if lane_i+1>=len(road.lane_section_list):
                        next_lane=None
                    else:
                        next_lane=road.lane_section_list[lane_i+1]
                    point_to_width=dict()
                    lane_seq=0
                    for lane in lane_section.left:
                            lane_seq=lane_seq+1
                            way_nodes_id = list()
                            for point in road.points:
                                dis=point.s
                                if lane_section.have_point(dis,next_lane):
                                    width=lane.get_width(dis-lane_section.s)
                                    offset=0
                                    if point in point_to_width:
                                        offset=point_to_width[point]
                                    point_to_width[point]=width+offset
                                    # width=0
                                    if lane.type == "driving":
                                        
                                        dx = cos(point.rad + pi / 2) * (offset+ (width / 2))
                                        dy = sin(point.rad + pi / 2) * ( offset+ (width / 2))
                                        _,_, n_left = lane_section.get_left_width()
                                        node=Node(-1,point.x + dx,point.y + dy,point.z,lane_width=width,heading=point.rad + pi / 2,
                                            road_id=road_id,lane_num=n_left,lane_seq=lane_seq,is_mid=(lane_seq==1)
                                        )
                                        new_node_id = self.add_node(node)
                                        node.node_id=new_node_id
                                        # print(new_node_id)
                                        if not (new_node_id in way_nodes_id): # not exists in current way_nodes_id
                                            way_nodes_id.append(new_node_id)
                            if len(way_nodes_id) > 0:
                                ws_left, wd_left, n_left = lane_section.get_left_width()
                                ws_right, wd_right, n_right = lane_section.get_right_width()
                                offset=width
                                way_nodes_id.reverse()
                                self.ways[way_id] = Way(
                                    way_id, way_nodes_id, width, offset, road.is_connection, road.style, n_left, n_right, ws_left, ws_right)
                                way_id += 1
                    road.start_rway_id = way_id
                    offset = 0
                    point_to_width=dict()
                    lane_seq=0
                    for lane in lane_section.right:
                            lane_seq=lane_seq+1
                            way_nodes_id = list()
                            for point in road.points:
                                dis=point.s
                                if lane_section.have_point(dis,next_lane):
                                    width=lane.get_width(dis-lane_section.s)
                                    offset=0
                                    if point in point_to_width:
                                        offset=point_to_width[point]
                                    point_to_width[point]=width+offset
                                    if lane.type == "driving":
                                        
                                        dx = cos(point.rad - pi / 2) * (offset+ (width / 2))
                                        dy = sin(point.rad - pi / 2) * ( offset+(width / 2))
                                        _,_, n_right = lane_section.get_right_width()
                                        node=Node(-1, point.x + dx,point.y + dy,point.z,lane_width=width,heading=point.rad - pi / 2,
                                            road_id=road_id,lane_num=n_right,lane_seq=lane_seq,is_mid=(lane_seq==1)
                                        )
                                        new_node_id = self.add_node(node)
                                        node.node_id=new_node_id

                                        # print(new_node_id)
                                        if not (new_node_id in way_nodes_id): # not exists in current way_nodes_id
                                            way_nodes_id.append(new_node_id)

                            if len(way_nodes_id) > 0:
                                ws_left, wd_left, n_left = lane_section.get_left_width()
                                ws_right, wd_right, n_right = lane_section.get_right_width()
                                # width = wd_left + wd_right

                                # offset = width/2 - wd_right
                                offset = width
                                self.ways[way_id] = Way(
                                    way_id, way_nodes_id, width, offset, road.is_connection, road.style, n_left, n_right, ws_left, ws_right)

                            # offset += width
                                way_id += 1
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


    



    def add_node(self, node):
        # search for dup
        near_node_ids = self.spindex.intersect((node.x, node.y, node.x, node.y))

        if len(near_node_ids) > 0: # dup exists
            # if the new node A is quite close to an existing node B, use B
            return near_node_ids[0]
        else:
            # add a new node
            self.nodes.append(node)
            self.spindex.insert(
                self.node_id, (node.x-self.min_distance, node.y-self.min_distance, node.x+self.min_distance, node.y+self.min_distance))
            self.node_id = self.node_id + 1
            return self.node_id - 1


    def generate_osm(self, filename, debug = False):

        wgs84_to_utm =Proj(proj='utm',zone=50,ellps='WGS84')
        base_utmx,base_utmy=wgs84_to_utm(self.opendrive.lon,self.opendrive.lat)
        if debug:
            for node in self.nodes:
                plt.plot(node.x, node.y, node.color)
            plt.show()
        
        csvfile = open(filename+"_main.csv", 'w')
        writer = csv.writer(csvfile)
        writer.writerow(['road_id', 'lon', 'lat','utmX','utmY','heading','mode','speed_mode','event_mode','oppsite_side_mode','lane_num','lane_seq','lane_width'])
        data = [ ]
        for index, way_id in enumerate(self.ways):
            way_value = self.ways[way_id]
            for way_node in way_value.nodes_id:
                node=self.nodes[way_node]
                if node.is_mid:
                    utmx,utmy=base_utmx+node.x,base_utmy+node.y
                    node_x,node_y= wgs84_to_utm(utmx,utmy,inverse=True)
                    

                    data.append((node.road_id,node_x,node_y,utmx,utmy,node.heading,0,3,0,0,node.lane_num,node.lane_seq,node.lane_width))
        writer.writerows(data)
        csvfile.close()
        csvfile = open(filename+"_lane.csv", 'w')
        writer = csv.writer(csvfile)
        writer.writerow(['road_id' ,'lane_seq','lon', 'lat','utmX','utmY'])
        data = [ ]
        for index, way_id in enumerate(self.ways):
            way_value = self.ways[way_id]
            for way_node in way_value.nodes_id:
                node=self.nodes[way_node]
                if not node.is_mid:
                    utmx,utmy=base_utmx+node.x,base_utmy+node.y
                    node_x,node_y= wgs84_to_utm(utmx,utmy,inverse=True)
                    data.append((node.road_id,node.lane_seq,node_x,node_y,utmx,utmy))
        writer.writerows(data)
        csvfile.close()


RESOURCE_PATH = "../resource/"

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A random road generator')
    parser.add_argument('--debug', type=bool, default=False, help='Is using debug mode')
    parser.add_argument('--input_file', type=str, default='test5.xodr', help='Input OpenDRIVE file name')
    parser.add_argument('--scale', type=int, default=10000, help='Scale of xodr file (in meter)')
    parser.add_argument('--precise', type=int, default=0.1, help='Precision of OSM file (in meter)')
    parser.add_argument('--output_file', type=str, default='example', help='Output OSM file name')
    args = parser.parse_args()
    print(args)

    print('Start converting file...')

    converter = Converter(RESOURCE_PATH + args.input_file, args.scale, args.precise)
    converter.generate_osm(RESOURCE_PATH + args.output_file, args.debug)

    print('All done')
