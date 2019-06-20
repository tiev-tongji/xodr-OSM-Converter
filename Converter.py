from __future__ import division, absolute_import, print_function
import xml.etree.ElementTree as ET
from math import fabs, sqrt
import matplotlib.pyplot as plt
from datetime import datetime

from osmtype import Node,Way

from opendrivepy.opendrive import OpenDrive
from opendrivepy.point import Point
from geompreds import orient2d, incircle

# To avoid the conflict between nodes
# Any points that is too close with peer ( < min distance ) are discarded
min_distance = 0.01 
def point_distance(pointa, pointb):
    return sqrt((pointa.x - pointb.x) ** 2 + (pointa.y - pointb.y) ** 2)

def node_distance(nodea, nodeb):
    return sqrt((nodea.x - nodeb.x) ** 2 + (nodea.y - nodeb.y) ** 2)

def line_cross(line1, line2):
    x1=line1[0].x
    y1=line1[0].y
    x2=line1[1].x
    y2=line1[1].y
    
    x3=line2[0].x
    y3=line2[0].y
    x4=line2[1].x
    y4=line2[1].y

    k1=(y2-y1)*1.0/(x2-x1)
    b1=y1*1.0-x1*k1*1.0
    if (x4-x3)==0:
        #L2直线斜率不存在操作
        k2=None
        b2=0
    else:
        k2=(y4-y3)*1.0/(x4-x3)
        #斜率存在操作
        b2=y3*1.0-x3*k2*1.0
    if k2==None:
        x=x3
    else:
        x=(b2-b1)*1.0/(k1-k2)
    y=k1*x*1.0+b1*1.0
    return [x,y]

def orient_node(nodea, nodeb, nodec):
    return orient2d( (nodea.x, nodea.y), (nodeb.x, nodeb.y), (nodec.x, nodec.y))

def find_diagonal(nodes):
    if orient_node(nodes[0], nodes[1], nodes[2]) * orient_node(nodes[3], nodes[1], nodes[2]) < 0:
        return 3
    elif orient_node(nodes[0], nodes[1], nodes[3]) * orient_node(nodes[2], nodes[1], nodes[3]) < 0:
        return 2
    else:
        return 1

    

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
                    found = False
                    for node in nodes:
                        if point_distance(node, point) < min_distance:
                            found = True
                            break

                    if found:
                        way_nodes_id.append(node.id)
                    else:
                        nodes.append(Node(node_id, point.x, point.y))
                        way_nodes_id.append(node_id)
                        node_id = node_id + 1
                    #     last_point = point

                    # if last_point is not None:
                    #     if point_distance(last_point, point) > min_distance:
                    #         # print(point_distance(last_point, point))
                    #         nodes.append(Node(node_id, point.x, point.y))
                    #         way_nodes_id.append(node_id)
                    #         node_id = node_id + 1
                    #         last_point = point
                    #     #else:
                    #     #    print("discarded")
                    # else:
                    #     #print("first point")
                    #     nodes.append(Node(node_id, point.x, point.y))
                    #     way_nodes_id.append(node_id)
                    #     node_id = node_id + 1
                    #     last_point = point

            if len(way_nodes_id) > 0:
                width = road.get_left_width() + road.get_right_width()
                offset = width/2 - road.get_right_width()
                ways[road_id] = Way(road_id,way_nodes_id,width, offset, road.is_connection, road.style)
        
        for junction in self.opendrive.junctions.values():
            if len(junction.lane_link) >= 2:
                # print(len(junction.lane_link))

                sum_x = 0
                sum_y = 0

                is_Tshape_junction = False
                is_Xshape_junction = False
                junction_center = None

                if len(junction.lane_link) == 3:
                    lane_link = junction.lane_link
                    line1_nodes = list()
                    line2_nodes = list()
                    for connection in junction.connections:
                        # add the contact point of '--' of a T junction
                        if ways[connection.connecting_road].style == 'line':
                            incoming_road = connection.incoming_road
                            connecting_road = connection.connecting_road
                            contact_point = connection.contact_point

                            way_node_index = (0 if contact_point == 'start' else -1)
                            node_index = ways[connecting_road].nodes_id[way_node_index]

                            distance_to_start = node_distance(nodes[node_index], nodes[ways[incoming_road].nodes_id[0]])
                            distance_to_end = node_distance(nodes[node_index], nodes[ways[incoming_road].nodes_id[-1]])

                            if distance_to_start < distance_to_end:
                                line1_nodes.append(nodes[ways[incoming_road].nodes_id[0]])
                                # ways[incoming_road].nodes_id.insert(0, node_id)
                                ways[incoming_road].nodes_id[0] = node_id
                            else:
                                line1_nodes.append(nodes[ways[incoming_road].nodes_id[-1]])
                                # ways[incoming_road].nodes_id.append(node_id)
                                ways[incoming_road].nodes_id[-1] = node_id
                            for i in range(len(lane_link)):
                                if lane_link[i][0] == incoming_road:
                                    del lane_link[i]
                                    break

                    if len(line1_nodes) >= 2:
                        is_Tshape_junction = True
                        # add two points of '|' of a T junction
                        for incoming_road, connecting_road, contact_point in lane_link:
                            way_node_index = (0 if contact_point == 'start' else -1)
                            node_index = ways[connecting_road].nodes_id[way_node_index]

                            distance_to_start = node_distance(nodes[node_index], nodes[ways[incoming_road].nodes_id[0]])
                            distance_to_end = node_distance(nodes[node_index], nodes[ways[incoming_road].nodes_id[-1]])
                            
                            if distance_to_start < distance_to_end:
                                line2_nodes.append(nodes[ways[incoming_road].nodes_id[0]])
                                line2_nodes.append(nodes[ways[incoming_road].nodes_id[1]])
                                ways[incoming_road].nodes_id[0] = node_id
                            else:
                                line2_nodes.append(nodes[ways[incoming_road].nodes_id[-1]])
                                line2_nodes.append(nodes[ways[incoming_road].nodes_id[-2]])
                                ways[incoming_road].nodes_id[-1] = node_id

                        # print(line1_nodes[0].id)
                        # print(line1_nodes[1].id)
                        # print(line2_nodes[0].id)
                        # print(line2_nodes[1].id)
                        # print('=' + str(node_id))
                        cross_point = line_cross(line1_nodes, line2_nodes)
                        nodes.append(Node(node_id, cross_point[0], cross_point[1], 10))
                        node_id = node_id + 1


                if len(junction.lane_link) == 4:
                    is_Xshape_junction = True
                    line_nodes = list()
                    for incoming_road, connecting_road, contact_point in junction.lane_link:
                        way_node_index = (0 if contact_point == 'start' else -1)
                        node_index = ways[connecting_road].nodes_id[way_node_index]

                        # add new node into incoming roads
                        distance_to_start = node_distance(nodes[node_index], nodes[ways[incoming_road].nodes_id[0]])
                        distance_to_end = node_distance(nodes[node_index], nodes[ways[incoming_road].nodes_id[-1]])
                        # print(min([distance_to_end, distance_to_start]))
                        if distance_to_start < distance_to_end:
                            line_nodes.append(nodes[ways[incoming_road].nodes_id[0]])
                            ways[incoming_road].nodes_id[0] = node_id
                        else:
                            line_nodes.append(nodes[ways[incoming_road].nodes_id[-1]])
                            ways[incoming_road].nodes_id[-1] = node_id
                    
                    diag_nodes = find_diagonal(line_nodes)
                    if diag_nodes != 1:
                        line_nodes[1], line_nodes[diag_nodes] = line_nodes[diag_nodes], line_nodes[1]
                    cross_point = line_cross(line_nodes[:2], line_nodes[2:])
                    nodes.append(Node(node_id, cross_point[0], cross_point[1], 10))
                    node_id = node_id + 1

                if not is_Tshape_junction and not is_Xshape_junction:

                    min_distance_to_center = 10
                    for incoming_road, connecting_road, contact_point in junction.lane_link:
                        way_node_index = (0 if contact_point == 'start' else -1)
                        node_index = ways[connecting_road].nodes_id[way_node_index]

                        # add new node into incoming roads
                        distance_to_start = node_distance(nodes[node_index], nodes[ways[incoming_road].nodes_id[0]])
                        distance_to_end = node_distance(nodes[node_index], nodes[ways[incoming_road].nodes_id[-1]])
                        # print(min([distance_to_end, distance_to_start]))
                        if distance_to_start < distance_to_end:
                            if distance_to_start < min_distance_to_center:
                                min_distance_to_center = distance_to_start
                            sub_node = nodes[ways[incoming_road].nodes_id[0]]
                            ways[incoming_road].nodes_id[0] = node_id
                        else:
                            if distance_to_end < min_distance_to_center:
                                min_distance_to_center = distance_to_end
                            sub_node = nodes[ways[incoming_road].nodes_id[-1]]
                            ways[incoming_road].nodes_id[-1] = node_id
                        # print(node_index)

                        # to calculate the center point of junctions
                        if not is_Tshape_junction:
                            sum_x += sub_node.x
                            sum_y += sub_node.y
                        
                    # print('=' + str(min_distance_to_center))
                    nodes.append(Node(node_id,sum_x / len(junction.lane_link), sum_y / len(junction.lane_link), min_distance_to_center))
                    # print("=" + str(node_id))
                    node_id = node_id + 1
            



           
        return ways, nodes

    def generate_osm(self, filename):
        osm_attrib = {'version': "0.6", 'generator': "xodr_OSM_converter", 'copyright': "Simon",
                        'attribution': "Simon", 'license': "GNU or whatever"}
        osm_root = ET.Element('osm', osm_attrib)

        bounds_attrib = {'minlat': '0', 'minlon': '0', 'maxlat': '1', 'maxlon': '1'}
        ET.SubElement(osm_root, 'bounds', bounds_attrib)

        for node in self.nodes:
            node_attrib = {'id': str(node.id), 'visible': 'true', 'version': '1', 'changeset': '1', 'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'), 'user': 'simon', 'uid': '1', 'lat': str(node.x / self.scale), 'lon': str(node.y / self.scale)}
            node_root = ET.SubElement(osm_root, 'node', node_attrib)
            ET.SubElement(node_root, 'tag', {'k': "type", 'v':'Crossing'})
            # if node.min_arc_radius != 0 :
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

Converter('./xodr/Town02.xodr', 0.01).generate_osm('./osm/Town02.osm')
