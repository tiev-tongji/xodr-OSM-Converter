import xml.etree.ElementTree as ET
import math
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


class Converter(object):
		"""docstring for Converter"""

		def __init__(self, filename):
			super(Converter, self).__init__()

			self.nodes = []
			self.ways = []
			node_id = 1

			tree = ET.parse(filename)
			root = tree.getroot()

			min_x, scale_x, min_y, scale_y = self.loc_scale(root)
			for road_root in root.iter('road'):

				way_nodes_id = []

				for geometry in root.iter('geometry'):
					geo_x = ((float(geometry.attrib['x']))-min_x)/scale_x
					geo_y = ((float(geometry.attrib['y']))-min_y)/scale_y

					node = Node(node_id, geo_x, geo_y)
					node_id = node_id + 1
					self.nodes.append(node)

					way_nodes_id.append(node.id)

				self.ways.append(Way(int(road_root.attrib['id']), way_nodes_id))

		def loc_scale(self, root):
			x = []
			y = []
			for geometry in root.iter('geometry'):
				x.append(float(geometry.attrib['x']))
				y.append(float(geometry.attrib['y']))
			min_x = min(x)
			min_y = min(y)
			scale_x = max(x) - min_x
			scale_y = max(y) - min_y
			return min_x, scale_x, min_y, scale_y

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
			tree = ET.ElementTree(osm_root)
			tree.write(filename)


Converter('Crossing8Course.xodr').generate_osm('Crossing8Course.osm')
