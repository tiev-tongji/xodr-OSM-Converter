from __future__ import division, absolute_import, print_function
import xml.etree.ElementTree as ET
from math import fabs
import matplotlib.pyplot as plt
from datetime import datetime

from osmtype import Node,Way

from opendrivepy.opendrive import OpenDrive
from opendrivepy.point import Point



class Converter(object):
    """docstring for Converter"""

    def __init__(self, filename, scene_scale):
        super(Converter, self).__init__()
        
        self.opendrive = OpenDrive(filename)
        self.scale = self.set_scale(scene_scale)
        self.ways, self.nodes = self.convert()



    def set_scale(self, scene_scale):
        # cast the bigger map into target boundary
        tar_scale = scene_scale # target boundary is [-tar_scale,tar_scale]
        x = []
        y = []
        length = []

        for road in self.opendrive.roads.values():
            for geometry in road.plan_view:
                x.append(geometry.x)
                y.append(geometry.y)
                length.append(geometry.length)

        scale = max([(max(x) - min(x)), (max(y) - min(y))])/tar_scale

        if scale == 0:
            scale = max(length)/tar_scale	
            
        return scale

    def convert(self):
        nodes = list()
        node_id = 0
        ways = dict()
        for road_id,road in self.opendrive.roads.items():
            way_nodes_id = list()
            for record in road.plan_view:
                if road.predecessor is None:
                    points = record.points[:-1]
                else:
                    points = record.points[1:-1]
                
                if road.successor is None:
                    points.append(record.points[-1])

                for point in points:
                    nodes.append(Node(node_id, point.x, point.y))
                    way_nodes_id.append(node_id)
                    node_id = node_id + 1
            ways[road_id] = Way(road_id, way_nodes_id)
            # print('insert' + str(id))

        # for road_id, road in self.opendrive.roads.items():
        #     if road.successor is not None:
        #         if road.successor.element_type == 'road':
        #             suc_begin_node = nodes[ways[road.successor.element_id].nodes_id[0]]
        #             suc_end_node = nodes[ways[road.successor.element_id].nodes_id[-1]]
                    
        #             end_node = nodes[ways[road_id].nodes_id[-1]]
        #             delta_begin = fabs(end_node.lat-suc_begin_node.lat) + fabs(end_node.lon - suc_begin_node.lon)
        #             delta_end = fabs(end_node.lat-suc_end_node.lat) + fabs(end_node.lon - suc_end_node.lon)
        #             if delta_begin < delta_end:
        #                 ways[road_id].nodes_id[-1] = ways[road.successor.element_id].nodes_id[0]
        #             else:
        #                 ways[road_id].nodes_id[-1] = ways[road.successor.element_id].nodes_id[-1]
                       
        #         elif road.successor.element_type == 'junction':
        #             pass 
        #     if road.predecessor is not None:
        #         if road.predecessor.element_type == 'road':
        #             suc_begin_node = nodes[ways[road.predecessor.element_id].nodes_id[0]]
        #             suc_end_node = nodes[ways[road.predecessor.element_id].nodes_id[-1]]
                    
        #             begin_node = nodes[ways[road_id].nodes_id[-1]]
        #             delta_begin = fabs(begin_node.lat-suc_begin_node.lat) + fabs(begin_node.lon - suc_begin_node.lon)
        #             delta_end = fabs(begin_node.lat-suc_end_node.lat) + fabs(begin_node.lon - suc_end_node.lon)
        #             if delta_begin < delta_end:
        #                 ways[road_id].nodes_id[0] = ways[road.predecessor.element_id].nodes_id[0]
        #             else:
        #                 ways[road_id].nodes_id[0] = ways[road.predecessor.element_id].nodes_id[-1]
                       
        #         elif road.predecessor.element_type == 'junction':
        #             pass 
        return ways, nodes

    def generate_osm(self, filename):
        osm_attrib = {'version': "0.6", 'generator': "xodr_OSM_converter", 'copyright': "Simon",
                        'attribution': "Simon", 'license': "GNU or whatever"}
        osm_root = ET.Element('osm', osm_attrib)

        bounds_attrib = {'minlat': '0', 'minlon': '0', 'maxlat': '1', 'maxlon': '1'}
        ET.SubElement(osm_root, 'bounds', bounds_attrib)

        for node in self.nodes:
            node_attrib = {'id': str(node.id), 'visible': node.visible, 'version': '1', 'changeset': '1', 'timestamp': datetime.utcnow(
            ).strftime('%Y-%m-%dT%H:%M:%SZ'), 'user': 'simon', 'uid': '1', 'lat': str(node.lat/self.scale), 'lon': str(node.lon/self.scale)}
            ET.SubElement(osm_root, 'node', node_attrib)

        for way_key, way_value in self.ways.items():
            way_attrib = {'id': str(way_key), 'visible': node.visible, 'version': '1', 'changeset': '1',
                                'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'), 'user': 'simon', 'uid': '1'}
            way_root = ET.SubElement(osm_root, 'way', way_attrib)
            for way_node in way_value.nodes_id:
                ET.SubElement(way_root, 'nd', {'ref': str(way_node)})
            ET.SubElement(way_root, 'tag', {'k': "highway", 'v':'tertiary'})
            ET.SubElement(way_root, 'tag', {'k': "name", 'v':'unknown road'})
        tree = ET.ElementTree(osm_root)
        tree.write(filename)


    # def show_road(self):

    # 	for road in opendrive.roads.values():
    # 		road.draw_road()
    # 			# plt.xlim(-210, 210)
    # 			# plt.ylim(-90, 90)

    # 	q = Point(-10, 0)
    # 	segment, right, left = opendrive.roadmap.closest_point(q)
    # 	point = segment.min_point(q)
    # 	distance = segment.min_distance(q)
    # 	plt.plot(q.x, q.y, 'g+')
    # 	plt.plot(point.x, point.y, 'r+')
    # 	#plt.ylim((15, -15))
    # 	#plt.xlim(198, 202)
    # 	plt.gca().set_aspect('equal', adjustable='box')
    # 	print(distance)
    # 	print(right, left)
    # 	plt.show()

Converter('./xodr/Crossing8Course.xodr', 0.01).generate_osm('./osm/Crossing8Course.osm')
