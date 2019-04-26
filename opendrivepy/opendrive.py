from __future__ import division, print_function, absolute_import


from opendrivepy.roadmap import RoadMap
import opendrivepy.xmlparser

import xml.etree.ElementTree as ET
from datetime import datetime

class OpenDrive(object):
    def __init__(self, file):
        parser = opendrivepy.xmlparser.XMLParser(file)
        self.header = None
        self.roads = parser.parse_roads()
        self.controllers = list()
        self.junctions = parser.parse_junctions()
        self.junction_groups = list()
        self.stations = list()
        self.roadmap = RoadMap(self.roads)



