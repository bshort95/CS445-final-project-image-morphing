import csv
from pathlib import Path

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from morph.correspondences import detect_face_landmarks


def draw_points(image, points, color=(0, 0, 255), radius=2):
    canvas = image.copy()
    for row, col in np.asarray(points, dtype=int):
        cv2.circle(canvas, (int(col), int(row)), radius, color, -1)
    return canvas


def draw_triangles(image, triangles, color=(255, 0, 0)):
    canvas = image.copy()
    for tri in triangles:
        pts = [(int(col), int(row)) for row, col in tri]
        cv2.line(canvas, pts[0], pts[1], color, 1)
        cv2.line(canvas, pts[1], pts[2], color, 1)
        cv2.line(canvas, pts[2], pts[0], color, 1)
    return canvas


def save_overlay(path, image):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), image)


def black_pixel_ratio(image, threshold=3):
    return float(np.mean(np.all(image <= threshold, axis=2)))


def landmark_alignment_error(image, expected_points):
    try:
        actual_points = detect_face_landmarks(image, include_boundary=False)
    except Exception:
        return float("nan")

    count = min(len(actual_points), len(expected_points))
    if count == 0:
        return float("nan")
    distances = np.linalg.norm(actual_points[:count] - expected_points[:count], axis=1)
    return float(np.mean(distances))


def write_metrics_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "mode",
        "frame",
        "point_count",
        "triangle_count",
        "black_pixel_ratio",
        "landmark_alignment_error",
        "generated_image",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def save_side_by_side(path, title, images):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, len(images), figsize=(5 * len(images), 5))
    if len(images) == 1:
        axes = [axes]
    for axis, (label, image) in zip(axes, images):
        axis.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        axis.set_title(label)
        axis.axis("off")
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def choose_side_by_side_frame_numbers(frame_count, include_endpoints=False):
    if frame_count <= 0:
        return []
    if include_endpoints and frame_count >= 3:
        return sorted({2, frame_count // 2 + 1, frame_count - 1})
    return sorted({1, (frame_count + 1) // 2, frame_count})


def evaluate_manual_vs_auto(
    img1,
    img2,
    manual_points1,
    manual_points2,
    auto_points1,
    auto_points2,
    manual_triangles,
    auto_triangles,
    manual_frame_paths,
    auto_frame_paths,
    output_dir="evaluation-results/manual-vs-auto",
    include_endpoints=False,
    blend_name=None,
):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    manual_tri1, manual_tri2 = manual_triangles
    auto_tri1, auto_tri2 = auto_triangles

    save_overlay(output_dir / "manual_source_landmarks.jpg", draw_points(img1, manual_points1))
    save_overlay(output_dir / "manual_destination_landmarks.jpg", draw_points(img2, manual_points2))
    save_overlay(output_dir / "auto_source_landmarks.jpg", draw_points(img1, auto_points1))
    save_overlay(output_dir / "auto_destination_landmarks.jpg", draw_points(img2, auto_points2))
    save_overlay(output_dir / "manual_source_triangulation.jpg", draw_triangles(img1, manual_tri1))
    save_overlay(output_dir / "manual_destination_triangulation.jpg", draw_triangles(img2, manual_tri2))
    save_overlay(output_dir / "auto_source_triangulation.jpg", draw_triangles(img1, auto_tri1))
    save_overlay(output_dir / "auto_destination_triangulation.jpg", draw_triangles(img2, auto_tri2))

    rows = []
    frame_count = max(len(manual_frame_paths), len(auto_frame_paths))
    auto_src_landmarks = detect_face_landmarks(img1, include_boundary=False)
    auto_dest_landmarks = detect_face_landmarks(img2, include_boundary=False)

    for mode, frame_paths, point_count, triangle_count in [
        ("manual", manual_frame_paths, len(manual_points1), len(manual_tri1)),
        ("auto", auto_frame_paths, len(auto_points1), len(auto_tri1)),
    ]:
        for frame_index, frame_path in enumerate(frame_paths, start=1):
            image = cv2.imread(str(frame_path))
            if include_endpoints:
                alpha = (frame_index - 1) / (frame_count - 1)
            else:
                alpha = frame_index / (frame_count + 2)
            expected = (1.0 - alpha) * auto_src_landmarks + alpha * auto_dest_landmarks
            rows.append(
                {
                    "mode": mode,
                    "frame": frame_index,
                    "point_count": point_count,
                    "triangle_count": triangle_count,
                    "black_pixel_ratio": black_pixel_ratio(image),
                    "landmark_alignment_error": landmark_alignment_error(image, expected),
                    "generated_image": str(frame_path),
                }
            )

    metrics_name = f"{blend_name}_metrics.csv" if blend_name else "metrics.csv"
    write_metrics_csv(output_dir / metrics_name, rows)

    if manual_frame_paths and auto_frame_paths:
        sample_frames = choose_side_by_side_frame_numbers(frame_count, include_endpoints)
        name_prefix = f"{blend_name}_" if blend_name else ""
        for frame_number in sample_frames:
            idx = frame_number - 1
            if idx < len(manual_frame_paths) and idx < len(auto_frame_paths):
                manual_image = cv2.imread(str(manual_frame_paths[idx]))
                auto_image = cv2.imread(str(auto_frame_paths[idx]))
                save_side_by_side(
                    output_dir / f"{name_prefix}side_by_side_frame_{frame_number}.png",
                    f"Manual vs Automatic Correspondences: Frame {frame_number}",
                    [("Manual", manual_image), ("Automatic", auto_image)],
                )

    return output_dir / metrics_name
