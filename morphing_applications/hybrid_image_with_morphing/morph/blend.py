import cv2


#####################################################################################
# function: laplacian_pyramid_blending
# Reading of input images and resizing them to same size
#
#####################################################################################
def laplacian_pyramid_blending(img1, img2, alpha, k,levels=5):
    gaussian1 = build_gaussian_pyramid(img1, levels)
    gaussian2 = build_gaussian_pyramid(img2, levels)

    laplacian1 = build_laplacian_pyramid(gaussian1)
    laplacian2 = build_laplacian_pyramid(gaussian2)

    selected_hybrid_items = []
    laplacian_blend = []
    level = 0  
    size = 0
   
    size = (img1.shape[1], img1.shape[0])

    level = 0
    for l1, l2 in zip(laplacian1, laplacian2):
        level+=1
        temp = (1-alpha)*l1 + alpha*l2   

        if (k == 1 and level == 1) or (k == 2 and level == 2) or (k == 3 and level == 3) or (k == 4 and level == 4):
            name="generated-images/laplacian-pyramid-blending/hipass/inter_hipass_"+str(k)+"_level_"+str(level)+".jpg"
            cv2.imwrite(name, temp) 
            selected_hybrid_items.append(temp)
        elif k == levels and level == levels+1:     
            name="generated-images/laplacian-pyramid-blending/hipass/inter_lowpass_"+str(k)+"_level_"+str(level)+".jpg"
            cv2.imwrite(name, temp) 
            # print(f"#####")
            selected_hybrid_items.append(temp)

        laplacian_blend.append(temp)
        # print(f"@@@@ ")

    # level = 0
    # for l1, l2 in zip(gaussian1, gaussian2):
    #    level+=1
    #    temp = (1-alpha)*l1 + alpha*l2   
    # #    print(f"@ k == {k} level == {level}")
    #    if k == levels and level == levels:
    #         name="generated-images/laplacian-pyramid-blending/hipass/inter_lowpass_"+str(k)+"_level_"+str(level)+".jpg"
    #         cv2.imwrite(name, temp) 
    #         # print(f"#####")
    #         selected_hybrid_items.append(temp)
    # #    print(f"&&&& ")     

    return reconstruct(laplacian_blend), selected_hybrid_items[0]

#################################################################
# function: build_gaussian_pyramid
# Build Gaussian pyramid of a provided image
# input parameters:
# img -- source image whose gaussian pyramid needs to be built
# levels -- total level of the pyramid
#################################################################
def build_gaussian_pyramid(img, level=5):
    G = [img]
    for _ in range(level):
        img = cv2.pyrDown(img)
        G.append(img)
    return G

#################################################################
# Function: build_laplacian_pyramid
# Build Laplacian pyramid based on gaussian pyramid
# Input parameter: gaussian_pyramid
#################################################################
def build_laplacian_pyramid(gaussian_pyramid):
    laplacian_pyramid = []
    for i in range(len(gaussian_pyramid)-1):
        size = (gaussian_pyramid[i].shape[1], gaussian_pyramid[i].shape[0])
        GE = cv2.pyrUp(gaussian_pyramid[i+1], dstsize=size)
        laplacian_pyramid.append(gaussian_pyramid[i] - GE)
    laplacian_pyramid.append(gaussian_pyramid[-1])
    return laplacian_pyramid


#################################################################
# Function: reconstruct
# Reconstruct the blended image
# Input parameter: gaussian_pyramid
#################################################################
def reconstruct(laplacian_pyramid):
    img = laplacian_pyramid[-1] 
    for i in range(len(laplacian_pyramid)-2, -1, -1):
        size = (laplacian_pyramid[i].shape[1], laplacian_pyramid[i].shape[0])
        img = cv2.pyrUp(img, dstsize=size) + laplacian_pyramid[i]
    return img   
    
###########################################################################################
# Function: reconstruct_hybrid_morphing_img_V3
# Reconstruct to generate the synthesized hybrid image
# Input parameter: 
# s_list -- the selected laplacian image from different level
# (Selection logic: level 1 img for first morph img, level 2 img for second morph img ....)
###########################################################################################
def reconstruct_hybrid_morphing_img_V3(s_list):
    current = s_list[-1]
    hi_pass = s_list[:-1]

    for i in reversed(range(len(hi_pass))):
        current = cv2.pyrUp(current)
        current = cv2.resize(
            current,
            (hi_pass[i].shape[1], hi_pass[i].shape[0])
        )
        current = current + hi_pass[i]

    return current



   
