from __future__ import division

import numpy as np




def subCell2DGenerator(arr, shape):
    '''
    generator to access evenly sized sub-cells in a 2d array
    returns indices and sub arrays as (i,j,sub)

    >>> a = np.array([[[0,1],[1,2]],[[2,3],[3,4]]])
    >>> gen = subCell2DGenerator(a,(2,2))
    >>> for i,j, sub in gen: print( i,j, sub )
    0 0 [[[0 1]]]
    0 1 [[[1 2]]]
    1 0 [[[2 3]]]
    1 1 [[[3 4]]]
    '''
    x,y=0,0
    g0,g1 = shape
    s0,s1 = arr.shape[:2]
    d0,d1 = int(round(s0/g0)),int(round(s1/g1))
    y1 = d0
    for i in range(g0):
        for j in range(g1):
            x1 = x+d1
            yield i,j, arr[y:y1,x:x1]
            x = x1
        y = y1
        y1 = y+d0
        x = 0


def subCell2DFnArray(arr, fn, cells, dtype=None):
    '''
    Return array where every cell is the output of a given cell function
    mx = subCell2DFnArray(myArray, np.max, (10,6) )
    --> here mx is a 2d array containing all cell maxima
    '''
    out = np.empty(shape=cells, dtype=dtype)
    for i,j,c in subCell2DGenerator(arr, cells):
        out[i,j] = fn(c)
    return out



if __name__ == '__main__':
    import doctest
    doctest.testmod()