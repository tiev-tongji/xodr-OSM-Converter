import xml.etree.ElementTree as ET
import math
import matplotlib.pyplot as plt
from datetime import datetime

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

	def __init__(self, way_id, nodes_id):
		super(Way, self).__init__()
		self.id = way_id

		self.nodes_id = nodes_id
		self.width = 1


class Converter(object):
	"""docstring for Converter"""

	def __init__(self, filename, scene_scale):
		super(Converter, self).__init__()

		self.nodes = []
		self.ways = []
		node_id = 1

		tree = ET.parse(filename)
		root = tree.getroot()

		self.scale = self.set_scale(root, scene_scale)
		for road_root in root.iter('road'):
			way_nodes_id = []

			for geometry in root.iter('geometry'):
				start_x = (float(geometry.attrib['x']))/self.scale
				start_y = (float(geometry.attrib['y']))/self.scale

				start_node = Node(node_id, start_x, start_y)
				# plt.plot(start_x, start_y, 'bo')
				self.nodes.append(start_node)
				way_nodes_id.append(start_node.id)
				node_id = node_id + 1

				if geometry[0].tag == 'line': # only insert start node
					pass

				elif geometry[0].tag == 'arc': # sampling and insert nodes
					curvature = float(geometry[0].attrib['curvature'])
					hdg = float(geometry.attrib['hdg'])
					noscale_length = float(geometry.attrib['length'])
					nodes_xy = self.arc_nodes(start_x, start_y, curvature, noscale_length, hdg)
					for xy in nodes_xy:
						arc_node = Node(node_id, xy[0], xy[1])
						# plt.plot(xy[0], xy[1], 'bo')
						self.nodes.append(arc_node)
						way_nodes_id.append(arc_node.id)
						node_id = node_id + 1

				elif geometry[0].tag == 'spiral': # sampling and insert nodes
					pass
				# geo_x = ((float(geometry.attrib['x']))-min_x)/scale
				# geo_y = ((float(geometry.attrib['y']))-min_y)/scale

				# node = Node(node_id, geo_x, geo_y)
				# node_id = node_id + 1
				# self.nodes.append(node)

				# way_nodes_id.append(node.id)
			end_x, end_y = self.get_road_end(geometry)
			end_node = Node(node_id, end_x, end_y)
			# plt.plot(end_x, end_y, 'bo')
			self.nodes.append(end_node)
			way_nodes_id.append(end_node.id)
			node_id = node_id + 1
			
			self.ways.append(Way(int(road_root.attrib['id']), way_nodes_id))
		# plt.show()

	def get_road_end(self, geometry):
		start_x = (float(geometry.attrib['x']))/self.scale
		start_y = (float(geometry.attrib['y']))/self.scale
		length = float(geometry.attrib['length'])/self.scale
		hdg = float(geometry.attrib['hdg'])

		if geometry[0].tag == 'line': # only insert start node
			end_x = start_x + length * math.cos(hdg)
			end_y = start_y + length * math.sin(hdg)

		elif geometry[0].tag == 'arc': # sampling and insert nodes
			curvature = float(geometry[0].attrib['curvature'])
			hdg = float(geometry.attrib['hdg'])

			radius = 1/curvature
			theta = length / radius
			l = 2 * math.sin(theta/2) * radius

			end_x = start_x +  l * math.cos(hdg)
			end_y = start_y +  l * math.sin(hdg)


		elif geometry[0].tag == 'spiral': # sampling and insert nodes
			end_x = start_x + length * math.cos(hdg)
			end_y = start_y + length * math.sin(hdg)
		return end_x, end_y

	def arc_nodes(self, start_x, start_y, curvature,length, hdg, sampling_length = None):
		nodes_xy = []

		if sampling_length is None:
			total_sampling = 20
		else:
			total_sampling = int(length / sampling_length)

		radius = 1/curvature
		theta = length / radius
		sampling_theta = theta / total_sampling
		l = 2 * math.sin(sampling_theta/2) * radius

		x = start_x
		y = start_y
		for i in range(total_sampling):
			dx = l * math.cos(hdg) / self.scale
			dy = l * math.sin(hdg) / self.scale
			x = x + dx
			y = y + dy
			hdg = hdg + sampling_theta
			nodes_xy.append([x,y])
		return nodes_xy


	def set_scale(self, root, scene_scale):
		# cast the bigger map into target boundary
		tar_scale = scene_scale # target boundary is [-tar_scale,tar_scale]
		x = []
		for geometry in root.iter('geometry'):
			x.append(float(geometry.attrib['x']))

		scale = (max(x) - min(x))/tar_scale
		return scale

	def generate_osm(self, filename):
		osm_attrib = {'version': "0.6", 'generator': "xodr_OSM_converter", 'copyright': "OpenStreetMap and contributors",
						'attribution': "http://www.openstreetmap.org/copyright", 'license': "http://opendatacommons.org/licenses/odbl/1-0/"}
		osm_root = ET.Element('osm', osm_attrib)

		bounds_attrib = {'minlat': '0', 'minlon': '0', 'maxlat': '1', 'maxlon': '1'}
		ET.SubElement(osm_root, 'bounds', bounds_attrib)

		for node in self.nodes:
			node_attrib = {'id': str(node.id), 'visible': node.visible, 'version': '1', 'changeset': '1', 'timestamp': datetime.utcnow(
			).strftime('%Y-%m-%dT%H:%M:%SZ'), 'user': 'simon', 'uid': '1', 'lat': str(node.lat), 'lon': str(node.lon)}
			ET.SubElement(osm_root, 'node', node_attrib)

		for way in self.ways:
			wat_attrib = {'id': str(way.id), 'visible': node.visible, 'version': '1', 'changeset': '1',
								'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'), 'user': 'simon', 'uid': '1'}
			way_root = ET.SubElement(osm_root, 'way', wat_attrib)
			for way_node in way.nodes_id:
				ET.SubElement(way_root, 'nd', {'ref': str(way_node)})
			ET.SubElement(way_root, 'tag', {'k': "highway", 'v':'tertiary'})
			ET.SubElement(way_root, 'tag', {'k': "name", 'v':'uknown road'})
		tree = ET.ElementTree(osm_root)
		tree.write(filename)

Converter('./xodr/Test_ToolRoadRunner.xodr', 0.01).generate_osm('./osm/Test_ToolRoadRunner.osm')
