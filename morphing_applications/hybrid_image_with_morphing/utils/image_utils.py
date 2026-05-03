import cv2
import numpy as np
import math
import sys

#####################################################################################
# To Calculate the circumcenter of the three points given. 
# 3 arguments as p1, p2 and p3.
# return type: coordinate of the the circumcenter of the point made by p1, p2 and p3.
#####################################################################################

def circumcenter(p1,p2,p3):
    
    #using the mathemathical formula for circumcenter for three points
    #Source for formula wikipedia
    
    d = 2 * (p1[0] * (p2[1] - p3[1]) + p2[0] * 
             (p3[1] - p1[1]) + p3[0] * (p1[1] - p2[1]))
    
    det_p1 = p1[0]**2 + p1[1]**2 
    det_p2 = p2[0]**2 + p2[1]**2
    det_p3 = p3[0]** 2 + p3[1]**2
    
    cx = (det_p1 * (p2[1] - p3[1]) 
          + det_p2 * (p3[1] - p1[1]) 
          + det_p3 * (p1[1] - p2[1])) / d
    
    cy = (det_p1 * (p3[0] - p2[0]) 
          + det_p2 * (p1[0] - p3[0]) 
          + det_p3 * (p2[0] - p1[0])) / d
    
    return (cx, cy)

#####################################################################################################
# To Calculate distance between two points 
# 2 arguments as p1 and p2.
# return type: float value of distance between p1 and p2 calculated using euclidean distance formula
#####################################################################################################

def dist(p1,p2):
    
    # Euclidean Distance formula
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 )

#######################################################################################################
# area(x1,y1,x2,y2,x3,y3)
#To Calculate Area of triangle
# This function takes 4 arguments such that (x1,y1), (x2,y2), (x3,y3) are co-ordinates of the triangle.
# return type: float value of area of triangle
#######################################################################################################

def area(x1, y1, x2, y2, x3, y3): 
    # formula to calculate area of triangle
    return abs((x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2)) / 2.0)
