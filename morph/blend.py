import cv2
import numpy as np

def cross_dissolve(img1, img2, alpha):
    return (1 - alpha) * img1 + alpha * img2

def laplacian_pyrimid_blending(img1, img2, alpha, levels=7):
    gaussian1 = build_gaussian_pyramid(img1, levels)
    gaussian2 = build_gaussian_pyramid(img2, levels)

    laplacian1 = build_laplacian_pyramid(gaussian1)
    laplacian2 = build_laplacian_pyramid(gaussian2)

    L_blend = []
    for l1, l2 in zip(laplacian1, laplacian2):
        L_blend.append((1-alpha)*l1 + alpha*l2)
        print(f"@@@@ ")

    return reconstruct(L_blend)


def build_gaussian_pyramid(img, levels=7):
    G = [img]
    for _ in range(levels):
        img = cv2.pyrDown(img)
        G.append(img)
    return G

def build_laplacian_pyramid(G):
    L = []
    for i in range(len(G)-1):
        size = (G[i].shape[1], G[i].shape[0])
        GE = cv2.pyrUp(G[i+1], dstsize=size)
        L.append(G[i] - GE)
    L.append(G[-1])
    return L

def reconstruct(L):
    img = L[-1]
    for i in range(len(L)-2, -1, -1):
        size = (L[i].shape[1], L[i].shape[0])
        img = cv2.pyrUp(img, dstsize=size) + L[i]
    return img    
