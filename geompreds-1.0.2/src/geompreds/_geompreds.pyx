exactinit(0)

cpdef _exactinit(bint verbose):
    """Initialise the predicate computation

    :param verbose: whether we want verbose information for initializing
    :type verbose: boolean
    """
    exactinit(verbose)

cpdef orient2d( pa,  pb,  pc):
    """Direction from pa to pc, via pb, where returned value is as follows:

    left : + [ = ccw ]
    straight : 0.
    right : - [ = cw ]

    :param pa: point
    :type pa: sequence
    :param pb: point
    :type pb: sequence
    :param pc: point
    :type pc: sequence
    :returns: double, twice signed area under triangle pa, pb, pc

    Its usage is as follows:

    :Example:

    >>> from geompreds import orient2d, incircle
    >>> orient2d( (0, 0), (10, 0), (10, 10)) # left turn, looking from above
    100.0
    >>> orient2d( (0, 0), (10, 0), (20, 0)) # straight
    0.0
    >>> orient2d( (0, 0), (10, 0), (10, -10)) # right turn, looking from above
    -100.0
    
    """
    return orient2d_(pa[0], pa[1],
                     pb[0], pb[1],
                     pc[0], pc[1])

cdef inline double orient2d_(double a, double b, double c, double d, double e, double f):
    cdef double result
    cdef double *p0 = [a, b] 
    cdef double *p1 = [c, d]
    cdef double *p2 = [e, f]
    return c_orient2d(p0, p1, p2)

cpdef incircle( pa,  pb,  pc,  pd):
    """Returns whether *pd* is in the circle defined by points *pa*, *pb*, *pc*

    :param pa: point
    :type pa: sequence
    :param pb: point
    :type pb: sequence
    :param pc: point
    :type pc: sequence
    :param pd: point
    :type pd: sequence
    :returns: double

    Its usage is as follows:

    :Example:
    
    >>> from geompreds import orient2d, incircle
    >>> incircle((0,0), (10,0), (0,10), (0,10)) # on boundary
    0.0
    >>> incircle((0,0), (10,0), (0,10), (1,1)) # inside, value positive
    1800.0
    >>> incircle((0,0), (10,0), (0,10), (-100,-100)) # outside, value negative
    -2200000.0
    
    """
    return incircle_(pa[0], pa[1], pb[0], pb[1], pc[0], pc[1], pd[0], pd[1]) 

cdef inline double incircle_(double a, double b, double c, double d, double e, double f, double g, double h):
    cdef double result
    cdef double *p0 = [a, b] 
    cdef double *p1 = [c, d]
    cdef double *p2 = [e, f]
    cdef double *p3 = [g, h]
    return c_incircle(p0, p1, p2, p3)
