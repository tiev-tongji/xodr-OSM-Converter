from geompreds import orient2d

def determinant(xa, ya, xb, yb, xc, yc):
    """Returns determinant of three points
    
    """
    return (xb - xa) * (yc - ya) - \
           (xc - xa) * (yb - ya)

def bigvalues():
    C = int(2e17)
    for i in range(0, 2048):
        ra = orient2d((0+C,0+C), (15+C, pow(10, -i)+C), (25+C,0+C))
        fa = determinant(0+C,0+C, 15+C, pow(10, -i)+C, 25+C, 0+C)
        try:
            assert ra == fa
        except AssertionError:
            print ra, "<>", fa, i, C

if __name__ == '__main__':
    assert orient2d( (0, 0), (0, 10), (-10, 10)) == 100.
    assert orient2d( (0, 0), (0, 10), (10, 10)) == -100.
    bigvalues()