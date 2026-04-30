import numpy as np
import math
import sys
import cv2

from morph.warp import warp_image_affine_transform_with_linear_dissolve
from morph.warp import warp_image_affine_transform_with_laplacian_pyrimid_blending
from morph.tps import warp_image_tps_with_linear_dissolve
from morph.tps import warp_image_tps_with_laplacian_pyrimid_blending
from morph.triangulation import compute_delaunay

#######################################################################################################################################
# CallBackFuncForimg1 
# To get callback coordinates and draw circle at points clicked in source image which are the control points in source image 
# CallBackFuncForimg2 
# To get callback coordinates and draw circle at points clicked in destination image which are the control points in source image
# getcoord
# To get the coordinates from the user using left mouse button click and storing that values in a list. One can select as many control points along with border points but it should be greater then 3
###########################################################################################################################################

def CallBackFuncForimg1(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        cv2.circle(im1, (x,y), 1, (0, 0, 255), 2)
        coordSrc.append((y,x))

def CallBackFuncForimg2(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        cv2.circle(im2, (x,y), 1, (255, 0, 0), 2)
        coordDest.append((y,x))
        
def getcoord(window,image):
    while (True):
        cv2.imshow(window, image)
        if cv2.waitKey(20) == 27:
            break
    cv2.destroyAllWindows()


def add_default_boundary_points(coord, image_shape):
    height, width = image_shape[:2]
    row_quarters = [0, height // 4, height // 2, (3 * height) // 4, height - 1]
    col_quarters = [0, width // 4, width // 2, (3 * width) // 4, width - 1]
    boundary_points = [
        (0, col_quarters[0]),
        (0, col_quarters[1]),
        (0, col_quarters[2]),
        (0, col_quarters[3]),
        (0, col_quarters[4]),
        (row_quarters[1], 0),
        (row_quarters[2], 0),
        (row_quarters[3], 0),
        (row_quarters[1], width - 1),
        (row_quarters[2], width - 1),
        (row_quarters[3], width - 1),
        (height - 1, col_quarters[0]),
        (height - 1, col_quarters[1]),
        (height - 1, col_quarters[2]),
        (height - 1, col_quarters[3]),
        (height - 1, col_quarters[4]),
    ]

    existing = set(coord)
    for point in boundary_points:
        if point not in existing:
            coord.append(point)
            existing.add(point)
    return coord

##############################################################################
# draw_delauany(img,triangleList,delaunay_color)
# To display the valid delaunany triangle in the image.
# Arguments:
# This function takes 3 arguments as img, triangleList and delaunay_color<br>
# img - The image on which we have to draw the triangles<br>
# triangleList - The list coordinates of the valid triangles.<br>
# delauany_color - the color of the lines of the triangles.
# 
# return type: 
# returns the image having the triangle.
##############################################################################     

def draw_delaunay(img, triangleList,delaunay_color):
    tri=[]
    
    for t in triangleList :
        
        pt1 = t[0]
        pt2 = t[1]
        pt3 = t[2]

        cv2.line(img, (pt1[1],pt1[0]), (pt2[1],pt2[0]), delaunay_color, 1)
        cv2.line(img, (pt2[1],pt2[0]), (pt3[1],pt3[0]), delaunay_color, 1)
        cv2.line(img, (pt3[1],pt3[0]), (pt1[1],pt1[0]), delaunay_color, 1)
        a=[]
        a.append(pt1)
        a.append(pt2)
        a.append(pt3)
        tri.append(a)
    return tri


##############################################################
# showTriangulated(img1,img2)
# To display the valid delaunany triangle in the image.
# Arguments:
# This function takes 2 arguments as img1 and img2
# img1 = source image
# img2 = destination image
# return type:
# returns the image having the triangle for further process.
################################################################     

def showTriangulated(img1,img2):
    size = img1.shape
    r = (0, 0, size[1], size[0])
    
    coord = coordSrc.copy()
    
    triangleList = compute_delaunay(coord)
    
    tri1 = draw_delaunay(img1,triangleList,(255,0,0))
    
    # Matching the point p0,..,pn of the source and destination image
    tri2 = []
    for i in range(len(tri1)):
        a = []
        for j in range(len(tri1[i])):
            a.append(coordDest[coordSrc.index(tri1[i][j])])
        tri2.append(a)
        
    tri2 = draw_delaunay(img2,tri2,(0,255,255))
    
    cv2.imshow("src",img1)
    cv2.imshow("dest",img2)
    cv2.imwrite("Triangulated Images/Triangulated Image_src.jpg",img1)
    cv2.imwrite("Triangulated Images/Triangulated Image_dest.jpg",img2)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return tri1,tri2

#################################################################
# Reading of input images and resizing them to same size
# img1=cv2.imread("bush.jpg")
# img2=cv2.imread("clinton.jpg")
#################################################################

if __name__ == "__main__":
    img1=cv2.imread("./input-images/"+ str(sys.argv[1]))
    img2=cv2.imread("./input-images/"+ str(sys.argv[2]))
    img2 = cv2.resize(img2,(img1.shape[1],img1.shape[0]))
    im1=np.copy(img1)
    im2=np.copy(img2)
    window1 = 'image1'
    window2= 'image2'
    coordSrc=[]
    coordDest=[]

    # # Getting control points on images using mouse click
    cv2.namedWindow(window1)
    cv2.setMouseCallback(window1, CallBackFuncForimg1)
    getcoord(window1,im1)

    cv2.namedWindow(window2)
    cv2.setMouseCallback(window2, CallBackFuncForimg2)
    getcoord(window2,im2)

    r1,c1,ch1= img1.shape
    r2,c2,ch2 = img2.shape

    if len(coordSrc) != len(coordDest):
        raise ValueError("Source and destination images must have the same number of control points.")
    if len(coordSrc) < 3:
        raise ValueError("At least 3 control points are required.")

    coordSrc = add_default_boundary_points(coordSrc, img1.shape)
    coordDest = add_default_boundary_points(coordDest, img2.shape)
    print("Added default boundary anchor points (corners plus quarter-edge anchors) to both images.")

    method = input(
        "Select morphing method ('affine-linear', 'affine-laplacian', 'tps-linear', 'tps-laplacian'): "
    ).strip().lower()
    no_of_intermed = int(input("Enter number of intermediate you want "))

    if method.startswith("affine"):
        # Triangulating the images and applying affine transformation
        tri1,tri2 = showTriangulated(im1,im2)
        print(f"@@ tri1 == {tri1}")
        print(f"@@ tri2 == {tri2}")

        if method == "affine-linear":
            warp_image_affine_transform_with_linear_dissolve(no_of_intermed, img1, img2, tri1, tri2)
        else:
            warp_image_affine_transform_with_laplacian_pyrimid_blending(no_of_intermed, img1, img2, tri1, tri2)
    elif method == "tps-linear":
        warp_image_tps_with_linear_dissolve(no_of_intermed, img1, img2, coordSrc, coordDest)
    elif method == "tps-laplacian":
        warp_image_tps_with_laplacian_pyrimid_blending(no_of_intermed, img1, img2, coordSrc, coordDest)
    else:
        raise ValueError("Unknown morphing method selected.")



