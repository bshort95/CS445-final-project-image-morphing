import cv2
import numpy as np
from utils.image_utils import area
from morph.blend import laplacian_pyrimid_blending

#######################################################################################################################################################
# ### isInsideTriangle(p1,p2,p3,x,y)
# 
# #### Use
# >To check if some point lie inside the triangle or not. 
# 
# #### Arguments
# >This function takes 8 arguments such that (x1,y1), (x2,y2), (x3,y3) are co-ordinates of the triangle and (x,y) is the point which we want to check.
# 
# #### return type 
# >bool value<br>
# >- True - point lies inside the triangle.<br>
# >- False - point doesn't lie inside the triangle.
#######################################################################################################################################################

def isInsideTriangle(p1,p2,p3,x,y):
 
    A = area (p1[0], p1[1], p2[0], p2[1], p3[0], p3[1])
    A1 = area (x, y, p2[0], p2[1], p3[0], p3[1])  
    A2 = area (p1[0], p1[1], x, y, p3[0], p3[1])  
    A3 = area (p1[0], p1[1], p2[0], p2[1], x, y)
    if(A == A1 + A2 + A3):
        return True
    else:
        return False


#########################################################################################
# ### get_affine_basis(coord)
# 
# #### Use
# >To Calculate the affine basis
# 
# #### Arguments
# >This function takes only 1 argument which contains the co-ordinates of the triangle 
# 
# #### return type 
# >float value of x and y component of both the affine basis of a triangle
########################################################################################     

def get_affine_basis(coord):
    e1x = coord[1][0]-coord[0][0]
    e1y = coord[1][1]-coord[0][1]
    e2x = coord[2][0]-coord[0][0]
    e2y = coord[2][1]-coord[0][1]
    return e1x,e1y,e2x,e2y

######################################################################################################################################
# ### get_intermediate_triangles(srcTri,destTri,k,n)
# 
# #### Use
# >To find the co-ordinates of the triangle in kth intermediate image corresponding to the triangle in Source and Destination Image.
# 
# #### Arguments
# >This function take 4 arguments <br>
# >- srcTri - coordinates of triangle in source image<br>
# >- destTri - coordinates of triangle in destination image<br>
# >- k - kth intermediate immage<br>
# >- n - k+2
# 
# #### return type
# >return the co-ordinates of the triangle in intermediate image by calculating it as:
#     
# <!-- $ \mathbf{Pk}= \left( \frac{n-k}{n} \right) \mathbf{P1}+\left(\frac{k}{n}\right)\mathbf{P2}$
# 
# $\mathbf{Pk}$ is calculated coordinate of triangle in intermediate kth image <br>
# $\mathbf{P1}$ is triangle coordinate in Source image<br>
# $\mathbf{P2}$ is triangle coordinate in Destination image      -->
##################################################################################################################################### 

def get_intermediate_triangles(srcTri , destTri , k , n):
    intTri=[]
    for (st,dt) in zip(srcTri,destTri):
        a=[]
        for (coordS,coordD) in zip(st,dt):
            
            xi=int(((n-k)/n)*coordS[0]+(k/n)*coordD[0])
            yi=int(((n-k)/n)*coordS[1]+(k/n)*coordD[1])
            a.append((xi,yi))
        intTri.append(a)
    return intTri


# ### checkRange(sx,sy,dx,dy)
# 
# #### Use
# >if sx,sy,dx,dy are out of range i.e if they are negative or greater than the size of image so this function normalize them
# 
# #### Arguments
# >This function take 4 arguments <br>
# >- (sx,sy) - coordinate in source image
# >- (dx,dy) - coordinate in destination image
# 
# #### return type
# >return the normalize co-ordinates    



def checkRange(sx , sy , dx , dy, img1, img2):
    if sx<0:
        sx=0
    if dx<0:
        dx=0
    if sy<0:
        sy=0
    if dy<0:
        dy=0
    if sx>img1.shape[0]-1:
        sx=img1.shape[0]-1
    if dx>img2.shape[0]-1:
        dx=img2.shape[0]-1
    if sy>img1.shape[1]-1:
        sy=img1.shape[1]-1
    if dy>img2.shape[1]-1:
        dy=img2.shape[1]-1
    return sx,sy,dx,dy
       
       
###############################################################################################################
# warp_image_affine_transform_with_laplacian_pyrimid_blending
# To do affine Transformation from source image to destination image with laplacian pyrimid blending
# Arguments:
# no_of_intermed -- how many number of intermediate images we want to make.
# img1 -- Source image
# img2 -- Target image
################################################################################################################ 

def warp_image_affine_transform_with_laplacian_pyrimid_blending(no_of_intermed, img1, img2, tri1, tri2):
    # n=no_of_intermed+2
    n=no_of_intermed
    
    selected_synthesize_items = []

    for k in range(1,no_of_intermed+1):
        
        print(str(k)+" intermediate is generating it may take some time Please Wait...")
        img1_warp = np.zeros_like(img1, dtype=np.float32)
        img2_warp = np.zeros_like(img2, dtype=np.float32)
        inter=np.zeros_like(img1,dtype=np.uint8)
        row,col,channel=inter.shape
        print(f"row == {row}, col == {col}, channel == {channel}")

        intTri=get_intermediate_triangles(tri1,tri2,k,n)
        
        print(f"@@@ intTri == {intTri}")

        for (s_tri , i_tri , d_tri) in zip(tri1 , intTri , tri2):

            src_e1x , src_e1y , src_e2x , src_e2y = get_affine_basis(s_tri)
            int_e1x , int_e1y , int_e2x , int_e2y = get_affine_basis(i_tri)
            dest_e1x , dest_e1y , dest_e2x , dest_e2y = get_affine_basis(d_tri)
            
            #print(f"debug 1")
            for r in range(row):
                for c in range(col):
                    if isInsideTriangle(i_tri[0],i_tri[1],i_tri[2],r,c):
                        # print("debug 3")
                        X = r-i_tri[0][0]
                        Y = c-i_tri[0][1]

                        alpha=((int_e2y*X)-(Y*int_e2x))/((int_e1x*int_e2y)-(int_e2x*int_e1y))
                        beta=((int_e1y*X)-(Y*int_e1x))/((int_e1y*int_e2x)-(int_e2y*int_e1x))

                        dest_x=int(alpha*dest_e1x+beta*dest_e2x+d_tri[0][0])
                        dest_y=int(alpha*dest_e1y+beta*dest_e2y+d_tri[0][1])

                        src_x=int(alpha*src_e1x+beta*src_e2x+s_tri[0][0])
                        src_y=int(alpha*src_e1y+beta*src_e2y+s_tri[0][1])

                        src_x,src_y,dest_x,dest_y=checkRange(src_x,src_y,dest_x,dest_y, img1, img2)

                        img1_warp[r][c] = img1[src_x][src_y]
                        img2_warp[r][c] = img2[dest_x][dest_y]

        alpha = k / n
        inter, synthsize_item = laplacian_pyrimid_blending(img1_warp, img2_warp, alpha, k)

        selected_synthesize_items.append(synthsize_item)

        inter = np.clip(inter, 0, 255).astype(np.uint8)

        # print(f"debug 2")
        name="generated-images/laplacian-pyrimid-blending/inter_"+str(k)+".jpg"
        cv2.imwrite(name, inter) 

    return selected_synthesize_items    
