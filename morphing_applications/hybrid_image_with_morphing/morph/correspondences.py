import numpy as np
import cv2

def get_manual_points(img1, img2):
    h, w = img1.shape[:2]
    points = np.array([[0,0],[w-1,0],[0,h-1],[w-1,h-1]], dtype=np.float32)
    return points, points.copy()

def get_orb_matches(img1, img2):
    orb = cv2.ORB_create()
    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(img2, None)

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)
    matches = sorted(matches, key=lambda x: x.distance)

    pts1 = np.float32([kp1[m.queryIdx].pt for m in matches])
    pts2 = np.float32([kp2[m.trainIdx].pt for m in matches])

    return pts1, pts2
