from __future__ import division, absolute_import, print_function
import xml.etree.ElementTree as ET
from math import fabs, sqrt
import matplotlib.pyplot as plt
from datetime import datetime

from osmtype import Node,Way

from opendrivepy.opendrive import OpenDrive
from opendrivepy.point import Point

# To avoid the conflict between nodes
# Any points that is too close with peer ( < min distance ) are discarded
min_distance = 0.01 
def point_distance(pointa, pointb):
    return sqrt((pointa.x - pointb.x) ** 2 + (pointa.y - pointb.y) ** 2)

def node_distance(nodea, nodeb):
    return sqrt((nodea.lat - nodeb.lat) ** 2 + (nodea.lon - nodeb.lon) ** 2)

class Converter(object):
    """docstring for Converter"""

    def __init__(self, filename, scene_scale):
        super(Converter, self).__init__()
        
        self.opendrive = OpenDrive(filename)
        self.scale = self.set_scale(scene_scale)
        # print(self.scale)
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

        scale = max([(max(x) - min(x)), (max(y) - min(y))]) / tar_scale

        if scale == 0:
            scale = max(length) / tar_scale	
            
        return scale

    
    def convert(self):
        nodes = list()
        node_id = 0
        ways = dict()
        for road_id, road in self.opendrive.roads.items():
            # if road.is_connection:
            #     continue
            way_nodes_id = list()
            last_point = None
            for record in road.plan_view:
                # print(road.get_left_width() + road.get_right_width())

                for point in record.points:
                    #print('\n')
                    #print("node_id = " + str(node_id))
                    if last_point is not None:
                        if point_distance(last_point, point) > min_distance:
                            # print(point_distance(last_point, point))
                            nodes.append(Node(node_id, point.x, point.y))
                            way_nodes_id.append(node_id)
                            node_id = node_id + 1
                            last_point = point
                        #else:
                        #    print("discarded")
                    else:
                        #print("first point")
                        nodes.append(Node(node_id, point.x, point.y))
                        way_nodes_id.append(node_id)
                        node_id = node_id + 1
                        last_point = point

            if len(way_nodes_id) > 0:
                width = road.get_left_width() + road.get_right_width()
                offset = width/2 - road.get_right_width()
                ways[road_id] = Way(road_id,way_nodes_id,width, offset, road.is_connection)
        
        for junction in self.opendrive.junctions.values():
            if len(junction.lane_link) == 4:
                sum_x = 0
                sum_y = 0
                for incoming_road, connecting_road, contact_point in junction.lane_link:
                    way_node_index = (0 if contact_point == 'start' else -1)
                    node_index = ways[connecting_road].nodes_id[way_node_index]
                    print(node_index)
                    
                    sum_x += nodes[node_index].lat
                    sum_y += nodes[node_index].lon
                    

                    distance_to_start = node_distance(nodes[node_index], nodes[ways[incoming_road].nodes_id[0]])
                    distance_to_end = node_distance(nodes[node_index], nodes[ways[incoming_road].nodes_id[-1]])
                    if distance_to_start < distance_to_end:
                        ways[incoming_road].nodes_id.insert(0, node_id)
                    else:
                        ways[incoming_road].nodes_id.append(node_id)
                nodes.append(Node(node_id,sum_x / 4, sum_y / 4))
                print("=" + str(node_id))
                node_id = node_id + 1
            



           
        return ways, nodes

    def generate_osm(self, filename):
        osm_attrib = {'version': "0.6", 'generator': "xodr_OSM_converter", 'copyright': "Simon",
                        'attribution': "Simon", 'license': "GNU or whatever"}
        osm_root = ET.Element('osm', osm_attrib)

        bounds_attrib = {'minlat': '0', 'minlon': '0', 'maxlat': '1', 'maxlon': '1'}
        ET.SubElement(osm_root, 'bounds', bounds_attrib)

        for node in self.nodes:
            node_attrib = {'id': str(node.id), 'visible': 'true', 'version': '1', 'changeset': '1', 'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'), 'user': 'simon', 'uid': '1', 'lat': str(node.lat / self.scale), 'lon': str(node.lon / self.scale)}
            node_root = ET.SubElement(osm_root, 'node', node_attrib)
            # ET.SubElement(node_root, 'tag', {'k': "type", 'v':'Junction'})
            ET.SubElement(node_root, 'tag', {'k': "minArcRadius", 'v': str(0)})

        for way_key, way_value in self.ways.items():
            if way_value.is_connecting:
                continue
            way_attrib = {'id': str(way_key),'version': '1', 'changeset': '1',
                                'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'), 'user': 'simon', 'uid': '1'}
            way_root = ET.SubElement(osm_root, 'way', way_attrib)
            for way_node in way_value.nodes_id:
                ET.SubElement(way_root, 'nd', {'ref': str(way_node)})
            # ET.SubElement(way_root, 'tag', {'k': "highway", 'v':'tertiary'})
            ET.SubElement(way_root, 'tag', {'k': "name", 'v':'road'+str(way_value.id)})
            ET.SubElement(way_root, 'tag', {'k': "streetWidth", 'v': str(way_value.width)})
            ET.SubElement(way_root, 'tag', {'k': "streetOffset", 'v': str(way_value.offset)})
            ET.SubElement(way_root, 'tag', {'k': "sidewalkWidthLeft", 'v': str(0)})
            ET.SubElement(way_root, 'tag', {'k': "sidewalkWidthRight", 'v': str(0)})
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
Converter('./xodr/Town03.xodr', 0.01).generate_osm('./osm/Town03.osm')
