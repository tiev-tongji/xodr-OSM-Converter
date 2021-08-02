from __future__ import division, print_function, absolute_import


class Lanes(object):
    def __init__(self, lane_section_list):
        self.lane_offset = None
        self.lane_section_list = lane_section_list
        


class LaneSection(object):
    def __init__(self, left, center, right,s=0):
        self.s=s
        self.left = left
        self.right = right
        self.center = center
        self.ln = 0
        self.rn = 0
        self.ldwidth = list()
        self.rdwidth = list()
        self.lswidth = list()
        self.rswidth = list()
        #准备删除
        for lane in self.left:
            if lane.type == "driving":
                self.ln += 1
                self.ldwidth.append(lane.width.a)
            elif lane.type == "sidewalk":
                self.lswidth.append(lane.width.a)
        #删除
        self.left.sort(key=lambda x:abs(int(x.id)))
        self.right.sort(key=lambda x:abs(int(x.id)))
        for lane in self.right:
            if lane.type == "driving":
                self.rn += 1
                self.rdwidth.append(lane.width.a)
            elif lane.type == "sidewalk":
                self.rswidth.append(lane.width.a)
    def have_point(self,dis,next_lane=None):
        if next_lane:
            if(dis>=self.s and dis <=next_lane.s):
                return True
            else:
                return False
        else:
            if dis>=self.s:
                return True
            else:
                return False
    


                    
                

    def get_left_width(self):
        swidth = 0
        dwidth = 0
        n = 0
        for lane in self.left:
            if lane.type == "driving":
                dwidth += lane.width.a
                n += 1
            elif lane.type == "sidewalk":
                swidth += lane.width.a

        return swidth, dwidth, n

    def get_right_width(self):
        swidth = 0
        dwidth = 0
        n = 0
        for lane in self.right:
            if lane.type == "driving":
                dwidth += lane.width.a
                n += 1
            elif lane.type == "sidewalk":
                swidth += lane.width.a

        return swidth, dwidth, n


class Lane(object):
    def __init__(self, id, type, level, predecessor, successor, width_list):
        # Attributes
        self.id = id
        self.type = type
        self.level = level

        # Elements
        self.predecessor = predecessor
        self.successor = successor
        self.width_list = width_list
        self.border = list()
        self.road_mark = list()

        self.material = list()
        self.visibility = list()
        self.speed = list()
        self.access = list()
        self.height = list()
        self.width=None
        for width in self.width_list:
            if width.a!=0 and abs(width.b)<0.01 and abs(width.c)<=0.01 and abs(width.d)<0.01:
                self.width=width
        if self.width==None and self.id !=0:
            if len(self.width_list):
                self.width=self.width_list[0]
    def get_width(self,dis):
        real_width=None
        for i,width in enumerate(self.width_list):
            if dis>=width.s_offset:
                if i+1<len(self.width_list):
                    if dis<self.width_list[i+1].s_offset:
                        real_width=width
                        break
                else:
                    real_width=width
                    break
        if real_width:
            return real_width.get_width(dis)
        return None


class LaneLink(object):
    def __init__(self, id):
        self.id = id


class LaneWidth(object):
    def __init__(self, s_offset, a, b, c, d):
        self.s_offset = s_offset
        self.a = a
        self.b = b
        self.c = c
        self.d = d
    def get_width(self,dis):
        ds=dis-self.s_offset
        width=self.a + self.b*ds + self.c*ds**2 + self.d*ds**3
        return width

