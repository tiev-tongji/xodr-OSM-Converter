import unittest
from geompreds import orient2d, incircle

class TestOrient2d(unittest.TestCase):

    def test_left(self):
        """Points make a left turn, area positive"""
        assert orient2d( (0, 0), (10, 0), (10, 10)) == 100.0

    def test_straight(self):
        """Points on a straight line, area zero"""
        assert orient2d( (0, 0), (10, 0), (20, 0)) == 0.0

    def test_right(self):
        """Points make a right turn, area negative"""
        assert orient2d( (0, 0), (10, 0), (10, -10))  == -100.0

class TestIncircle(unittest.TestCase):

    def test_onboundary(self):
        """Point on boundary of circle, zero"""
        assert incircle((0,0), (10,0), (0,10), (0,10)) == 0.

    def test_inside(self):
        """Point inside circle, positive value returned"""
        assert incircle((0,0), (10,0), (0,10), (1,1)) == 1800. 

    def test_outside(self):
        """Point outside circle, negative value returned"""
        assert incircle((0,0), (10,0), (0,10), (-100,-100)) == -2200000.0 

if __name__ == '__main__':
    unittest.main()