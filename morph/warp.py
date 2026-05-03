from pathlib import Path

import cv2
import numpy as np
from utils.image_utils import area
from morph.blend import laplacian_pyramid_blending

def get_affine_basis(coord):
    e1x = coord[1][0]-coord[0][0]
    e1y = coord[1][1]-coord[0][1]
    e2x = coord[2][0]-coord[0][0]
    e2y = coord[2][1]-coord[0][1]
    return e1x,e1y,e2x,e2y

def isInsideTriangle(p1,p2,p3,x,y):
 
    A = area (p1[0], p1[1], p2[0], p2[1], p3[0], p3[1])
    A1 = area (x, y, p2[0], p2[1], p3[0], p3[1])  
    A2 = area (p1[0], p1[1], x, y, p3[0], p3[1])  
    A3 = area (p1[0], p1[1], p2[0], p2[1], x, y)
    if(A == A1 + A2 + A3):
        return True
    else:
        return False
    
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

def _row_col_to_xy(triangle):
    tri = np.asarray(triangle, dtype=np.float32)
    return np.column_stack([tri[:, 1], tri[:, 0]]).astype(np.float32)


def get_intermediate_triangles(srcTri, destTri, k, n):
    intTri = []
    for st, dt in zip(srcTri, destTri):
        tri = []
        for coordS, coordD in zip(st, dt):
            xi = int(((n - k) / n) * coordS[0] + (k / n) * coordD[0])
            yi = int(((n - k) / n) * coordS[1] + (k / n) * coordD[1])
            tri.append((xi, yi))
        intTri.append(tri)
    return intTri


def _apply_affine_triangle(src, dst, src_tri, dst_tri):
    src_xy = _row_col_to_xy(src_tri)
    dst_xy = _row_col_to_xy(dst_tri)
    if abs(cv2.contourArea(dst_xy)) < 1.0:
        return

    src_rect = cv2.boundingRect(src_xy)
    dst_rect = cv2.boundingRect(dst_xy)
    sx, sy, sw, sh = src_rect
    dx, dy, dw, dh = dst_rect

    if sw <= 0 or sh <= 0 or dw <= 0 or dh <= 0:
        return

    src_crop = src[sy : sy + sh, sx : sx + sw]
    if src_crop.size == 0:
        return

    src_offset = src_xy - np.array([sx, sy], dtype=np.float32)
    dst_offset = dst_xy - np.array([dx, dy], dtype=np.float32)
    transform = cv2.getAffineTransform(src_offset, dst_offset)
    warped = cv2.warpAffine(
        src_crop,
        transform,
        (dw, dh),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT_101,
    )

    mask = np.zeros((dh, dw, 3), dtype=np.float32)
    cv2.fillConvexPoly(mask, np.int32(dst_offset), (1.0, 1.0, 1.0), 16, 0)
    dst_slice = dst[dy : dy + dh, dx : dx + dw]
    dst[dy : dy + dh, dx : dx + dw] = dst_slice * (1.0 - mask) + warped * mask


def _warp_to_intermediate(img, src_triangles, intermediate_triangles):
    warped = np.zeros_like(img, dtype=np.float32)
    src_float = img.astype(np.float32)
    for src_tri, inter_tri in zip(src_triangles, intermediate_triangles):
        _apply_affine_triangle(src_float, warped, src_tri, inter_tri)
    return warped


def _write_frame(output_dir, frame_index, frame):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    path = output_path / f"inter_{frame_index}.jpg"
    cv2.imwrite(str(path), frame)
    return path


def _generate_frames(no_of_frames, img1, img2, tri1, tri2, output_dir, blend, include_endpoints=False):
    frame_paths = []
    if include_endpoints and no_of_frames < 2:
        raise ValueError("At least two total frames are required when endpoints are included.")

    for frame_index in range(1, no_of_frames + 1):
        if include_endpoints:
            alpha = (frame_index - 1) / (no_of_frames - 1)
            k = frame_index - 1
            n = no_of_frames - 1
        else:
            n = no_of_frames + 2
            k = frame_index
            alpha = k / n

        print(f"{frame_index} frame is generating...")
        if include_endpoints and frame_index == 1:
            inter = img1.copy()
        elif include_endpoints and frame_index == no_of_frames:
            inter = img2.copy()
        else:
            int_tri = get_intermediate_triangles(tri1, tri2, k, n)
            img1_warp = _warp_to_intermediate(img1, tri1, int_tri)
            img2_warp = _warp_to_intermediate(img2, tri2, int_tri)
            if blend == "linear":
                inter = (1.0 - alpha) * img1_warp + alpha * img2_warp
            else:
                inter = laplacian_pyramid_blending(img1_warp, img2_warp, alpha)
            inter = np.clip(inter, 0, 255).astype(np.uint8)

        frame_paths.append(_write_frame(output_dir, frame_index, inter))

    return frame_paths


def warp_image_affine_transform_with_linear_dissolve(
    no_of_intermed,
    img1,
    img2,
    tri1,
    tri2,
    output_dir="generated-images/linear-dissolve",
    include_endpoints=False,
):
    return _generate_frames(no_of_intermed, img1, img2, tri1, tri2, output_dir, "linear", include_endpoints)


def warp_image_affine_transform_with_laplacian_pyramid_blending(
    no_of_intermed,
    img1,
    img2,
    tri1,
    tri2,
    output_dir="generated-images/laplacian-pyramid-blending",
    include_endpoints=False,
):
    return _generate_frames(no_of_intermed, img1, img2, tri1, tri2, output_dir, "laplacian", include_endpoints)
