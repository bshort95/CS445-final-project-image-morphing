import numpy as np
import math
import sys
import cv2

from morph.warp import warp_image_affine_transform_with_laplacian_pyrimid_blending
from morph.blend import reconstruct_hybrid_morphing_img_V3
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
    # img1=cv2.imread("./input-images/"+ str(sys.argv[1]), cv2.IMREAD_GRAYSCALE)
    # img2=cv2.imread("./input-images/"+ str(sys.argv[2]), cv2.IMREAD_GRAYSCALE)
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
    # img2 = np.stack((img2,)*3, axis=-1)
    r2,c2,ch2 = img2.shape

    # Triangulating the images and applying affine transformation
    tri1,tri2 = showTriangulated(im1,im2)
    print(f"@@ tri1 == {tri1}")
    print(f"@@ tri2 == {tri2}")
    # warp_image_affine_transform_with_linear_dissolve(int(input("Enter number of intermediate you want ")), img1, img2, tri1, tri2)
    selected_synthesize_items = warp_image_affine_transform_with_laplacian_pyrimid_blending(int(input("Enter number of intermediate you want ")), img1, img2, tri1, tri2)

    print(f"@@@ selected_synthesize_items. len == {len(selected_synthesize_items)}")
    synthsize_hybrid_morphing_img = reconstruct_hybrid_morphing_img_V3(selected_synthesize_items)
    hybrid_morphing_name="generated-images/laplacian-pyrimid-blending/output/hybrid_morph_blending_result.jpg"
    cv2.imwrite(hybrid_morphing_name, synthsize_hybrid_morphing_img)