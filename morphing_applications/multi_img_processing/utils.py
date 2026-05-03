import numpy as np
import math
import sys
import cv2
import os

from morph.warp import get_intermediate_triangles, get_affine_basis, isInsideTriangle,checkRange
from morph.triangulation import compute_delaunay


coord=[]
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


def CallBackFuncForimg(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        cv2.circle(param, (x,y), 1, (255, 255, 255), 2)
        coord.append((y,x))

def getcoord(window,image):
    while (True):
        cv2.imshow(window, image)
        if cv2.waitKey(20) == 27:
            break
    cv2.destroyAllWindows()


def write_trig_files (imgs):
    trig_list = []
    count = 0
    for i in imgs:
        coord.clear()
        windowName = "image{0}".format(count)
        cv2.namedWindow(windowName)
        cv2.setMouseCallback(windowName, CallBackFuncForimg, i)   
        getcoord(windowName,i)
        trig_list.append(coord.copy())
        count = count + 1
    write_count = 0
    print(trig_list)
    for t in trig_list:
        fout = open('./morphing_applications/multi_img_processing/trig-files/trig{0}'.format(write_count), "w")
        for i in t:
            fout.write(str(i))
            fout.write('\n')
        fout.close
        write_count = write_count + 1

def get_multi_input_images(dir):
    imgs = []
    resized_imgs = []
    img_folder = dir 

    for img in os.listdir(img_folder):
        temp_img = cv2.imread(img_folder + img)
        imgs.append(temp_img)

    base_h, base_w, base_c = imgs[0].shape

    for img in imgs:
        resized_imgs.append(cv2.resize(img,(base_h,base_w)))

    return resized_imgs

def read_trig_files():
    trig_list = []
    read_count = 0
    trig_folder = './morphing_applications/multi_img_processing/trig-files' # Current directory

    for trig in os.listdir(trig_folder): 
        temp_list = []
        with open(trig_folder + '/trig{0}'.format(read_count), "r") as fin:
            for x in fin:
                temp = x.strip() 
                var1 = int(temp.split(', ')[0][1:])
                var2 = int(temp.split(', ')[1][:-1])
                temp_list.append((var1,var2)) 
        read_count = read_count + 1
        trig_list.append(temp_list.copy())
        temp_list.clear()
    return trig_list

def show_triangulated_for_muliple_imgs(imgs,trigs):
    size = imgs[0].shape
    r = (0, 0, size[1], size[0])
    base_trig = trigs[0]
    base_triangleList = compute_delaunay(base_trig)
    del_base = imgs[0].copy()
    base_tri = draw_delaunay(del_base,base_triangleList,(0,0,0))
    tri_list = [base_tri]
    del_list = [del_base]
    for x in range(len(imgs) -1):
         # Matching the point p0,..,pn of the source and destination image
        second_tri = []
        for i in range(len(base_tri)):
            a = []
            for j in range(len(base_tri[i])):
                a.append(trigs[x+1][base_trig.index(base_tri[i][j])])
            second_tri.append(a)
        temp_del = imgs[x+1].copy()        
        tri_list.append(draw_delaunay(temp_del,second_tri,(0,0,0)))
        del_list.append(temp_del)
    for x in range(len(imgs)):
        cv2.imshow("img{0}".format(x),del_list[x])
        cv2.imwrite("./morphing_applications/multi_img_processing/multi-input-triangulated-imgs/img{0}.jpg".format(x),del_list[x])    
    
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return tri_list

def get_intermediate_triangle(tris):
    intTri=[]
    print(tris)
    for x in range(len(tris[0])):
        tri_level = [item[x] for item in tris]

        a = []
        for y in range(len(tris)):
            tup_level =  [coord[y] for coord in tri_level]
            xi = int(np.mean([coord[0] for coord in tup_level]))        
            yi = int(np.mean([coord[1] for coord in tup_level]))
            a.append((xi,yi))
        intTri.append(a)


    return intTri
    



def create_avg_img(imgs,tris):
    
    base_img = imgs[0]        
    inter=np.zeros_like(base_img,dtype=np.uint8)
    row,col,channel=inter.shape

    int_tri=get_intermediate_triangle(tris)
    frame_count = 0
    print(f"@@@ intTri == {int_tri}")
    averaged_imgs = []
    for w in range(len(imgs)):
        inter=np.zeros_like(base_img,dtype=np.uint8)
        print(f"working on img {w}")
        for ( s_tri , i_tri , d_tri ) in zip( tris[w] , int_tri , int_tri ):
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

                        src_x,src_y,dest_x,dest_y=checkRange(src_x,src_y,dest_x,dest_y, imgs[w], imgs[w])

                        inter[r][c][0]=int(((3-1)/3)*imgs[w][src_x][src_y][0])
                        inter[r][c][1]=int(((3-1)/3)*imgs[w][src_x][src_y][1])
                        inter[r][c][2]=int(((3-1)/3)*imgs[w][src_x][src_y][2])
        
#         cv2.imshow("inter"+str(k),inter)
            # print(f"debug 2")
        averaged_imgs.append(inter)
    
    avg_image = np.mean(averaged_imgs, axis=0).astype(np.uint8)
    name="./morphing_applications/multi_img_processing/multi-input-generated-imgs/averged_image.jpg"
    cv2.imwrite(name, avg_image) 
       # cv2.waitKey(0)
       # cv2.destroyAllWindows()

def warp_image_affine_transform_multiple_imgs(no_of_intermed, imgs,tris):
    n=no_of_intermed+2
    base_img = imgs[0]
    frame_count = 0
    
    for x in range(len(imgs)-1):
        img1 = imgs[x]
        img2 = imgs[x+1]
        tri1 = tris[x]
        tri2 = tris[x+1]
        
        for k in range(1,no_of_intermed+1):
            


            print(str(k)+f" of image{x} and  image{x +1} intermediate is generating it may take some time Please Wait...")
            inter=np.zeros_like(base_img,dtype=np.uint8)
            row,col,channel=inter.shape
            print(f"row == {row}, col == {col}, channel == {channel}")

            intTri=get_intermediate_triangles(tri1,tri2,k,n)
            
            print(f"@@@ intTri == {intTri}")

            for ( s_tri , i_tri , d_tri ) in zip( tri1 , intTri , tri2 ):

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

                            inter[r][c][0]=int(((n-k)/n)*img1[src_x][src_y][0]
                                            +(k/n)*img2[dest_x][dest_y][0])
                            inter[r][c][1]=int(((n-k)/n)*img1[src_x][src_y][1]
                                            +(k/n)*img2[dest_x][dest_y][1])
                            inter[r][c][2]=int(((n-k)/n)*img1[src_x][src_y][2]
                                            +(k/n)*img2[dest_x][dest_y][2])

#         cv2.imshow("inter"+str(k),inter)
            # print(f"debug 2")
            name="./morphing_applications/multi_img_processing/multi-input-generated-imgs/inter_"+str(frame_count)+".jpg"
            cv2.imwrite(name, inter) 
            frame_count = frame_count + 1
       # cv2.waitKey(0)
       # cv2.destroyAllWindows()