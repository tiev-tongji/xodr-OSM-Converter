import xml.etree.ElementTree as ET
tree = ET.parse('Crossing8Course.xodr')
root = tree.getroot()

for child in root:
	if child.tag == 'controller':
		continue
	if child.tag == 'road':
		print child.tag, child.attrib
		for subchild in child:
			print subchild.tag, subchild.attrib
	print child.tag, child.attrib