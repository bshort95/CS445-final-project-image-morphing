import json
from pathlib import Path

import cv2
import numpy as np


# Stable semantic subset from MediaPipe Face Mesh. The points cover the face
# outline, brows, eyes, nose, and lips while keeping triangulation manageable.
FACE_MESH_LANDMARK_INDICES = [
    10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379,
    378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127,
    162, 21, 54, 103, 67, 109, 70, 63, 105, 66, 107, 336, 296, 334, 293, 300,
    33, 246, 161, 160, 159, 158, 157, 173, 263, 466, 388, 387, 386, 385, 384,
    398, 133, 155, 154, 153, 145, 144, 163, 362, 382, 381, 380, 374, 373, 390,
    1, 2, 98, 327, 168, 197, 195, 5, 4, 45, 275, 220, 440, 48, 278, 61, 146,
    91, 181, 84, 17, 314, 405, 321, 375, 291, 78, 95, 88, 178, 87, 14, 317,
    402, 318, 324, 308, 0, 13, 82, 312,
]


def _load_mediapipe():
    try:
        import mediapipe as mp
    except ImportError as exc:
        raise RuntimeError(
            "MediaPipe is required for automatic facial correspondences. "
            "Install dependencies with: pip install -r requirements.txt"
        ) from exc
    return mp


def boundary_anchors(image_shape):
    h, w = image_shape[:2]
    return np.array(
        [
            (0, 0),
            (0, w - 1),
            (h - 1, 0),
            (h - 1, w - 1),
            (0, w // 2),
            (h - 1, w // 2),
            (h // 2, 0),
            (h // 2, w - 1),
        ],
        dtype=np.float32,
    )


def get_manual_points(img1, img2):
    points1 = boundary_anchors(img1.shape)
    points2 = boundary_anchors(img2.shape)
    return points1, points2


def detect_face_landmarks(img, include_boundary=True, landmark_indices=None):
    mp = _load_mediapipe()
    indices = landmark_indices or FACE_MESH_LANDMARK_INDICES
    h, w = img.shape[:2]
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    with mp.solutions.face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
    ) as face_mesh:
        result = face_mesh.process(rgb)

    if not result.multi_face_landmarks:
        raise ValueError("No face was detected in the image.")

    landmarks = result.multi_face_landmarks[0].landmark
    points = []
    for idx in indices:
        lm = landmarks[idx]
        row = int(round(lm.y * (h - 1)))
        col = int(round(lm.x * (w - 1)))
        row = int(np.clip(row, 0, h - 1))
        col = int(np.clip(col, 0, w - 1))
        points.append((row, col))

    points = np.array(points, dtype=np.float32)
    if include_boundary:
        points = np.vstack([points, boundary_anchors(img.shape)])
    return points


def get_automatic_face_points(img1, img2, include_boundary=True):
    points1 = detect_face_landmarks(img1, include_boundary=include_boundary)
    points2 = detect_face_landmarks(img2, include_boundary=include_boundary)
    return remove_duplicate_correspondences(points1, points2)


def remove_duplicate_correspondences(points1, points2):
    points1 = np.asarray(points1, dtype=np.float32)
    points2 = np.asarray(points2, dtype=np.float32)
    if len(points1) != len(points2):
        raise ValueError("Source and destination correspondence lists must have equal length.")

    seen = set()
    keep = []
    for idx, point in enumerate(points1):
        key = tuple(np.rint(point).astype(int))
        if key not in seen:
            seen.add(key)
            keep.append(idx)
    return points1[keep], points2[keep]


def save_correspondences(path, points1, points2, metadata=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": metadata or {},
        "coordinate_format": "row_col",
        "source_points": np.asarray(points1, dtype=float).tolist(),
        "destination_points": np.asarray(points2, dtype=float).tolist(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_correspondences(path):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    points1 = np.array(payload["source_points"], dtype=np.float32)
    points2 = np.array(payload["destination_points"], dtype=np.float32)
    return remove_duplicate_correspondences(points1, points2)


def get_orb_matches(img1, img2):
    orb = cv2.ORB_create()
    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(img2, None)
    if des1 is None or des2 is None:
        return np.empty((0, 2), dtype=np.float32), np.empty((0, 2), dtype=np.float32)

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = sorted(bf.match(des1, des2), key=lambda x: x.distance)
    pts1 = np.float32([(kp1[m.queryIdx].pt[1], kp1[m.queryIdx].pt[0]) for m in matches])
    pts2 = np.float32([(kp2[m.trainIdx].pt[1], kp2[m.trainIdx].pt[0]) for m in matches])
    return remove_duplicate_correspondences(pts1, pts2)
