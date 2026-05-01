import numpy as np
from scipy.spatial import Delaunay

from utils.image_utils import circumcenter
from utils.image_utils import dist
from utils.image_utils import area

############################################################################################################################
# delaunay(pts,coord)
# To check whether the three points passed in pts form a triangle according to delaunay condition or not 
# Arguments:
# This function takes 2 arguments as pts and coord.
# pts - contains three points that represent the coordinates of the triangle on which the condition is to be checked.
# coord - all the points the are input by the user as well as the boundary points.
# return type:
# boolean value - whether the passed triangle points fulfill the delauny conditon or not
# True - Fulfiled<br>
# False - Not Fulfiled
#############################################################################################################################

def delaunay(pts,coord):
    
    # Checking weather the points are collinear or not
    area_tri = area(pts[0][0],pts[0][1],pts[1][0],pts[1][1],pts[2][0],pts[2][1])
    if area_tri == 0:
        return False
        
    # Finding the circumcenter of the selected points for triangle
    c = circumcenter(pts[0],pts[1],pts[2])
    
    #radius of the circumcircle by p1,p2,p3
    radius = dist(c,pts[0])

    #Getting the distance of remaining points and checking delaunay condition
    
    for i in range(len(coord)):
        if coord[i] not in pts:
            d = dist(c,coord[i])
            if d < radius:
                return False
    
    return True


#######################################################################################
# combinations(coord)
# To generate the combinations of points to create triangles.
# Arguments:
# This function takes 1 arguments coord
# coord - the list of points provided by the user for the delaunay triangulation.
# return type: 
# returns the list of all the combinations of the points.
######################################################################################     

def combinations(coord):
    comb = []
    for i in range(len(coord)):
        for j in range(i + 1, len(coord)):
            for k in range(j + 1, len(coord)):
                t = (coord[i], coord[j], coord[k])
                comb.append(t)
    return comb
                    

#########################################################################################
# compute_delaunay(coord)
# To check which combinations of points satisfy the delaunay condition. 
# Arguments: This function takes 1 arguments coord
# coord - the list of points provided by the user for the delaunay triangulation.
# return type: 
# returns the list of the combinations of the points that satisfy the delaunay condition
#########################################################################################     

def compute_delaunay(coord):  
    comb = combinations(coord)
    triangle_list = []
    for i in comb:
        cond = delaunay(i,coord)
        if cond == True:
            triangle_list.append(i)
            
    return triangle_list


def compute_delaunay_scipy(coord):
    points = np.asarray(coord, dtype=np.float32)
    if len(points) < 3:
        raise ValueError("At least three points are required for Delaunay triangulation.")

    # SciPy expects Cartesian x/y coordinates. The project stores points as
    # row/col, so swap columns only for triangulation and return row/col tuples.
    xy_points = np.column_stack([points[:, 1], points[:, 0]])
    delaunay_result = Delaunay(xy_points)
    triangles = []
    for simplex in delaunay_result.simplices:
        tri = [tuple(points[idx].astype(int)) for idx in simplex]
        if area(tri[0][0], tri[0][1], tri[1][0], tri[1][1], tri[2][0], tri[2][1]) > 0:
            triangles.append(tri)
    return triangles


def triangulate_correspondences(points1, points2, method="custom"):
    points1 = np.asarray(points1, dtype=np.float32)
    points2 = np.asarray(points2, dtype=np.float32)
    if len(points1) != len(points2):
        raise ValueError("Source and destination correspondence lists must have equal length.")

    if method == "scipy":
        triangles1 = compute_delaunay_scipy(points1)
    else:
        coord = [tuple(point.astype(int)) for point in points1]
        triangles1 = compute_delaunay(coord)

    lookup = {tuple(point.astype(int)): tuple(points2[idx].astype(int)) for idx, point in enumerate(points1)}
    triangles2 = []
    for tri in triangles1:
        try:
            triangles2.append([lookup[tuple(point)] for point in tri])
        except KeyError as exc:
            raise ValueError("Triangulation produced a point without a destination match.") from exc
    return triangles1, triangles2

