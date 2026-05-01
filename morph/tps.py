import os

import cv2
import numpy as np

from morph.blend import laplacian_pyrimid_blending


def _as_float_points(points):
    pts = np.asarray(points, dtype=np.float64)
    if pts.ndim != 2 or pts.shape[1] != 2:
        raise ValueError("Control points must have shape (N, 2).")
    return pts


def _kernel(r2):
    safe_r2 = np.maximum(r2, 1e-12)
    values = safe_r2 * np.log(safe_r2)
    values[r2 <= 1e-12] = 0.0
    return values


def solve_tps_parameters(source_points, target_points, regularization=1e-5):
    src = _as_float_points(source_points)
    dst = _as_float_points(target_points)

    if src.shape != dst.shape:
        raise ValueError("Source and target control points must have the same shape.")
    if src.shape[0] < 3:
        raise ValueError("Thin Plate Spline requires at least 3 control points.")

    n_points = src.shape[0]
    diff = src[:, None, :] - src[None, :, :]
    r2 = np.sum(diff * diff, axis=2)
    k_matrix = _kernel(r2)
    k_matrix += np.eye(n_points) * regularization

    p_matrix = np.concatenate((np.ones((n_points, 1)), src), axis=1)
    upper = np.concatenate((k_matrix, p_matrix), axis=1)
    lower = np.concatenate((p_matrix.T, np.zeros((3, 3))), axis=1)
    system = np.concatenate((upper, lower), axis=0)

    rhs_x = np.concatenate((dst[:, 0], np.zeros(3)))
    rhs_y = np.concatenate((dst[:, 1], np.zeros(3)))

    params_x = np.linalg.solve(system, rhs_x)
    params_y = np.linalg.solve(system, rhs_y)

    return {
        "control_points": src,
        "weights_x": params_x[:n_points],
        "affine_x": params_x[n_points:],
        "weights_y": params_y[:n_points],
        "affine_y": params_y[n_points:],
    }


def evaluate_tps_map(parameters, query_points):
    ctrl = parameters["control_points"]
    query = _as_float_points(query_points)

    diff = query[:, None, :] - ctrl[None, :, :]
    r2 = np.sum(diff * diff, axis=2)
    basis = _kernel(r2)
    affine = np.concatenate((np.ones((query.shape[0], 1)), query), axis=1)

    mapped_x = basis @ parameters["weights_x"] + affine @ parameters["affine_x"]
    mapped_y = basis @ parameters["weights_y"] + affine @ parameters["affine_y"]

    return np.stack((mapped_x, mapped_y), axis=1)


def get_intermediate_points(source_points, target_points, k, n):
    src = _as_float_points(source_points)
    dst = _as_float_points(target_points)
    alpha = k / n
    return (1.0 - alpha) * src + alpha * dst


def _build_query_grid(height, width):
    rows, cols = np.indices((height, width), dtype=np.float64)
    return np.stack((rows.ravel(), cols.ravel()), axis=1)


def _sample_image_bilinear(image, sample_points):
    height, width = image.shape[:2]

    rows = np.clip(sample_points[:, 0], 0, height - 1)
    cols = np.clip(sample_points[:, 1], 0, width - 1)

    row0 = np.floor(rows).astype(np.int32)
    col0 = np.floor(cols).astype(np.int32)
    row1 = np.clip(row0 + 1, 0, height - 1)
    col1 = np.clip(col0 + 1, 0, width - 1)

    dr = rows - row0
    dc = cols - col0

    top_left = image[row0, col0].astype(np.float64)
    top_right = image[row0, col1].astype(np.float64)
    bottom_left = image[row1, col0].astype(np.float64)
    bottom_right = image[row1, col1].astype(np.float64)

    top = (1.0 - dc)[:, None] * top_left + dc[:, None] * top_right
    bottom = (1.0 - dc)[:, None] * bottom_left + dc[:, None] * bottom_right
    return (1.0 - dr)[:, None] * top + dr[:, None] * bottom


def warp_image_with_tps(image, source_points, target_points, regularization=1e-5):
    height, width = image.shape[:2]
    params = solve_tps_parameters(target_points, source_points, regularization=regularization)
    query = _build_query_grid(height, width)
    sample_points = evaluate_tps_map(params, query)
    warped = _sample_image_bilinear(image, sample_points)
    return warped.reshape(height, width, image.shape[2])


def warp_image_tps_with_linear_dissolve(no_of_intermed, img1, img2, points1, points2):
    n = no_of_intermed + 2
    os.makedirs("generated-images/tps-linear-dissolve", exist_ok=True)

    for k in range(1, no_of_intermed + 1):
        print(str(k) + " TPS intermediate is generating. Please wait...")
        intermediate_points = get_intermediate_points(points1, points2, k, n)
        img1_warp = warp_image_with_tps(img1, points1, intermediate_points)
        img2_warp = warp_image_with_tps(img2, points2, intermediate_points)
        alpha = k / n
        inter = (1.0 - alpha) * img1_warp + alpha * img2_warp
        inter = np.clip(inter, 0, 255).astype(np.uint8)

        name = "generated-images/tps-linear-dissolve/inter_" + str(k) + ".jpg"
        cv2.imwrite(name, inter)


def warp_image_tps_with_laplacian_pyrimid_blending(no_of_intermed, img1, img2, points1, points2):
    n = no_of_intermed + 2
    os.makedirs("generated-images/tps-laplacian-pyrimid-blending", exist_ok=True)

    for k in range(1, no_of_intermed + 1):
        print(str(k) + " TPS intermediate is generating. Please wait...")
        intermediate_points = get_intermediate_points(points1, points2, k, n)
        img1_warp = warp_image_with_tps(img1, points1, intermediate_points)
        img2_warp = warp_image_with_tps(img2, points2, intermediate_points)
        alpha = k / n
        inter = laplacian_pyrimid_blending(img1_warp, img2_warp, alpha)
        inter = np.clip(inter, 0, 255).astype(np.uint8)

        name = "generated-images/tps-laplacian-pyrimid-blending/inter_" + str(k) + ".jpg"
        cv2.imwrite(name, inter)
