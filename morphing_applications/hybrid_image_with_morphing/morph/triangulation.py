import cv2
import numpy as np

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
        for j in range(len(coord)):
            for k in range(len(coord)):
                if(i!=j&j!=k&k!=i):
                    t = (coord[i],coord[j],coord[k])
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

