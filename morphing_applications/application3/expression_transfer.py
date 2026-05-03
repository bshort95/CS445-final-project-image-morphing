import argparse
import json
import os
import sys
from pathlib import Path

import cv2
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from morph.tps import warp_image_with_tps


def read_image(path):
    image = cv2.imread(str(path))
    if image is None:
        raise FileNotFoundError(f"Could not read image: {path}")
    return image


def resize_like(image, reference):
    if image.shape[:2] == reference.shape[:2]:
        return image
    return cv2.resize(image, (reference.shape[1], reference.shape[0]))


def scale_points(points, from_shape, to_shape):
    if from_shape[:2] == to_shape[:2]:
        return points
    row_scale = to_shape[0] / from_shape[0]
    col_scale = to_shape[1] / from_shape[1]
    scaled = np.asarray(points, dtype=np.float64).copy()
    scaled[:, 0] *= row_scale
    scaled[:, 1] *= col_scale
    return scaled


def scale_box(box, from_shape, to_shape):
    corners = np.asarray([[box[0], box[1]], [box[2], box[3]]], dtype=np.float64)
    scaled = scale_points(corners, from_shape, to_shape)
    return normalize_box([scaled[0, 0], scaled[0, 1], scaled[1, 0], scaled[1, 1]])


def load_points(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        data = data.get("points", data.get("landmarks"))

    points = np.asarray(data, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 2:
        raise ValueError(f"Point file must contain a list of [row, col] pairs: {path}")
    return points


def save_points(path, points):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {"points": np.asarray(points, dtype=float).tolist()}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def load_box(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = data.get("box", data.get("roi"))
    box = np.asarray(data, dtype=np.float64)
    if box.shape != (4,):
        raise ValueError(f"Box file must contain [row0, col0, row1, col1]: {path}")
    return box


def save_box(path, box):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {"box": np.asarray(box, dtype=float).tolist()}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def make_display_image(image, max_display_size):
    height, width = image.shape[:2]
    max_width, max_height = max_display_size
    scale = min(max_width / width, max_height / height, 1.0)
    if scale == 1.0:
        return image.copy(), scale
    display = cv2.resize(image, (int(round(width * scale)), int(round(height * scale))))
    return display, scale


def normalize_box(box):
    row0, col0, row1, col1 = box
    top = min(row0, row1)
    bottom = max(row0, row1)
    left = min(col0, col1)
    right = max(col0, col1)
    return np.asarray([top, left, bottom, right], dtype=np.float64)


def points_to_box_normalized(points, box):
    box = normalize_box(box)
    top, left, bottom, right = box
    height = max(bottom - top, 1.0)
    width = max(right - left, 1.0)
    normalized = np.asarray(points, dtype=np.float64).copy()
    normalized[:, 0] = (normalized[:, 0] - top) / height
    normalized[:, 1] = (normalized[:, 1] - left) / width
    return normalized


def box_normalized_to_points(normalized_points, box):
    box = normalize_box(box)
    top, left, bottom, right = box
    height = max(bottom - top, 1.0)
    width = max(right - left, 1.0)
    points = np.asarray(normalized_points, dtype=np.float64).copy()
    points[:, 0] = top + points[:, 0] * height
    points[:, 1] = left + points[:, 1] * width
    return points


def collect_face_box(image, window_name, max_display_size):
    display, scale = make_display_image(image, max_display_size)
    start = None
    current = None
    final_box = None
    drawing = False

    def square_box(p0, p1):
        x0, y0 = p0
        x1, y1 = p1
        side = max(abs(x1 - x0), abs(y1 - y0))
        x_sign = 1 if x1 >= x0 else -1
        y_sign = 1 if y1 >= y0 else -1
        x2 = int(np.clip(x0 + x_sign * side, 0, display.shape[1] - 1))
        y2 = int(np.clip(y0 + y_sign * side, 0, display.shape[0] - 1))
        return x0, y0, x2, y2

    def redraw():
        canvas = display.copy()
        cv2.rectangle(canvas, (0, 0), (canvas.shape[1], 30), (255, 255, 255), -1)
        cv2.putText(
            canvas,
            f"{window_name}: drag square around face | Enter accept | r reset",
            (8, 21),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (20, 20, 20),
            1,
            cv2.LINE_AA,
        )
        if start is not None and current is not None:
            x0, y0, x1, y1 = square_box(start, current)
            cv2.rectangle(canvas, (x0, y0), (x1, y1), (0, 255, 255), 2)
        return canvas

    def on_mouse(event, x, y, flags, param):
        nonlocal start, current, final_box, drawing
        if event == cv2.EVENT_LBUTTONDOWN:
            start = (x, y)
            current = (x, y)
            final_box = None
            drawing = True
        elif event == cv2.EVENT_MOUSEMOVE and drawing:
            current = (x, y)
        elif event == cv2.EVENT_LBUTTONUP and drawing:
            current = (x, y)
            x0, y0, x1, y1 = square_box(start, current)
            final_box = normalize_box([y0 / scale, x0 / scale, y1 / scale, x1 / scale])
            drawing = False
            print(
                f"{window_name}: selected box "
                f"row0={final_box[0]:.1f}, col0={final_box[1]:.1f}, "
                f"row1={final_box[2]:.1f}, col1={final_box[3]:.1f}"
            )

    print(f"\nSelecting face box for: {window_name}")
    print("Drag a square around the face. Press Enter to accept, r to reset.")
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, display.shape[1], display.shape[0])
    cv2.setMouseCallback(window_name, on_mouse)
    while True:
        cv2.imshow(window_name, redraw())
        key = cv2.waitKey(30) & 0xFF
        if key in (13, 27, ord("q")) and final_box is not None:
            break
        if key == ord("r"):
            start = None
            current = None
            final_box = None
            drawing = False
            print(f"{window_name}: reset box")
    cv2.destroyWindow(window_name)
    return final_box


def collect_points(image, window_name, max_display_size):
    display, scale = make_display_image(image, max_display_size)
    points = []

    def redraw():
        canvas = display.copy()
        for index, point in enumerate(points, start=1):
            x = int(round(point[1] * scale))
            y = int(round(point[0] * scale))
            cv2.circle(canvas, (x, y), 3, (0, 0, 255), -1)
            cv2.putText(
                canvas,
                str(index),
                (x + 5, y - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (0, 0, 255),
                1,
                cv2.LINE_AA,
            )
        cv2.rectangle(canvas, (0, 0), (canvas.shape[1], 30), (255, 255, 255), -1)
        cv2.putText(
            canvas,
            f"{window_name}: {len(points)} pts | click add, u undo, Enter/Esc finish",
            (8, 21),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (20, 20, 20),
            1,
            cv2.LINE_AA,
        )
        return canvas

    def on_click(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            original_y = y / scale
            original_x = x / scale
            points.append([original_y, original_x])
            print(f"{window_name}: added point {len(points)} at row={original_y:.1f}, col={original_x:.1f}")

    print(f"\nSelecting landmarks for: {window_name}")
    print("Click points in order. Press u to undo. Press Enter or Esc when finished.")
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, display.shape[1], display.shape[0])
    cv2.setMouseCallback(window_name, on_click)
    while True:
        cv2.imshow(window_name, redraw())
        key = cv2.waitKey(30) & 0xFF
        if key in (13, 27, ord("q")):
            break
        if key == ord("u") and points:
            removed = points.pop()
            print(f"{window_name}: removed point at row={removed[0]:.1f}, col={removed[1]:.1f}")
    cv2.destroyWindow(window_name)
    return np.asarray(points, dtype=np.float64)


def add_boundary_anchors(points, image_shape):
    height, width = image_shape[:2]
    row_quarters = [0, height // 4, height // 2, (3 * height) // 4, height - 1]
    col_quarters = [0, width // 4, width // 2, (3 * width) // 4, width - 1]
    boundary = np.asarray(
        [
            [0, col_quarters[0]],
            [0, col_quarters[1]],
            [0, col_quarters[2]],
            [0, col_quarters[3]],
            [0, col_quarters[4]],
            [row_quarters[1], 0],
            [row_quarters[2], 0],
            [row_quarters[3], 0],
            [row_quarters[1], width - 1],
            [row_quarters[2], width - 1],
            [row_quarters[3], width - 1],
            [height - 1, col_quarters[0]],
            [height - 1, col_quarters[1]],
            [height - 1, col_quarters[2]],
            [height - 1, col_quarters[3]],
            [height - 1, col_quarters[4]],
        ],
        dtype=np.float64,
    )
    return np.vstack([points, boundary])


def validate_landmarks(target_points, driver_neutral_points, driver_expression_points):
    if target_points.shape != driver_neutral_points.shape:
        raise ValueError("Target and driver-neutral point lists must have the same shape.")
    if driver_neutral_points.shape != driver_expression_points.shape:
        raise ValueError("Driver-neutral and driver-expression point lists must have the same shape.")
    if target_points.shape[0] < 3:
        raise ValueError("At least 3 corresponding landmarks are required.")


def transfer_expression_with_boxes(
    target_neutral,
    target_points,
    target_box,
    driver_neutral_points,
    driver_neutral_box,
    driver_expression_points,
    driver_expression_box,
    strength=1.0,
    face_only=True,
):
    validate_landmarks(target_points, driver_neutral_points, driver_expression_points)

    target_normalized = points_to_box_normalized(target_points, target_box)
    driver_neutral_normalized = points_to_box_normalized(driver_neutral_points, driver_neutral_box)
    driver_expression_normalized = points_to_box_normalized(driver_expression_points, driver_expression_box)

    expression_offsets = driver_expression_normalized - driver_neutral_normalized
    target_expression_normalized = target_normalized + strength * expression_offsets
    target_expression_points = box_normalized_to_points(target_expression_normalized, target_box)

    source_points = add_boundary_anchors(target_points, target_neutral.shape)
    destination_points = add_boundary_anchors(target_expression_points, target_neutral.shape)

    full_warp = warp_image_with_tps(target_neutral, source_points, destination_points)
    full_warp = np.clip(full_warp, 0, 255).astype(np.uint8)
    if face_only:
        warped = blend_face_region(target_neutral, full_warp, target_points, target_expression_points)
    else:
        warped = full_warp
    return warped, full_warp, target_expression_points


def transfer_expression(
    target_neutral,
    target_points,
    driver_neutral_points,
    driver_expression_points,
    strength=1.0,
    face_only=True,
):
    validate_landmarks(target_points, driver_neutral_points, driver_expression_points)

    expression_offsets = driver_expression_points - driver_neutral_points
    target_expression_points = target_points + strength * expression_offsets

    source_points = add_boundary_anchors(target_points, target_neutral.shape)
    destination_points = add_boundary_anchors(target_expression_points, target_neutral.shape)

    full_warp = warp_image_with_tps(target_neutral, source_points, destination_points)
    full_warp = np.clip(full_warp, 0, 255).astype(np.uint8)
    if face_only:
        warped = blend_face_region(target_neutral, full_warp, target_points, target_expression_points)
    else:
        warped = full_warp
    return warped, full_warp, target_expression_points


def blend_face_region(original, warped, source_points, destination_points):
    mask_points = np.vstack([source_points, destination_points]).astype(np.float32)
    hull = cv2.convexHull(mask_points)

    mask = np.zeros(original.shape[:2], dtype=np.float32)
    cv2.fillConvexPoly(mask, hull.astype(np.int32), 1.0)

    height, width = mask.shape
    kernel_size = max(21, int(round(min(height, width) * 0.06)))
    if kernel_size % 2 == 0:
        kernel_size += 1

    mask = cv2.GaussianBlur(mask, (kernel_size, kernel_size), 0)
    mask = np.clip(mask, 0.0, 1.0)[:, :, None]
    blended = mask * warped.astype(np.float32) + (1.0 - mask) * original.astype(np.float32)
    return np.clip(blended, 0, 255).astype(np.uint8)


def draw_landmark_arrows(image, start_points, end_points):
    vis = image.copy()
    for start, end in zip(start_points, end_points):
        p0 = (int(round(start[1])), int(round(start[0])))
        p1 = (int(round(end[1])), int(round(end[0])))
        cv2.circle(vis, p0, 2, (255, 0, 0), -1)
        cv2.arrowedLine(vis, p0, p1, (0, 0, 255), 1, tipLength=0.25)
    return vis


def make_comparison(target_neutral, transferred, arrows):
    label_height = 32
    images = [target_neutral, transferred, arrows]
    labeled = []
    labels = ["target neutral", "transferred expression", "landmark motion"]
    for image, label in zip(images, labels):
        canvas = np.full((image.shape[0] + label_height, image.shape[1], 3), 255, dtype=np.uint8)
        canvas[label_height:] = image
        cv2.putText(canvas, label, (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (20, 20, 20), 1, cv2.LINE_AA)
        labeled.append(canvas)
    return np.hstack(labeled)


def make_difference_view(original, transferred):
    diff = cv2.absdiff(original, transferred)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    scaled = np.clip(gray.astype(np.float32) * 8.0, 0, 255).astype(np.uint8)
    return cv2.applyColorMap(scaled, cv2.COLORMAP_JET)


def print_motion_stats(target_points, target_expression_points):
    displacement = target_expression_points - target_points
    distances = np.linalg.norm(displacement, axis=1)
    print(
        "Landmark motion after strength scaling: "
        f"mean={distances.mean():.2f}px, max={distances.max():.2f}px"
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Transfer a driver's expression onto a target face using TPS landmark displacement."
    )
    parser.add_argument("--target-neutral", required=True, help="Target face image that receives the expression.")
    parser.add_argument("--driver-neutral", required=True, help="Driver face image with neutral expression.")
    parser.add_argument("--driver-expression", required=True, help="Driver face image with the expression to transfer.")
    parser.add_argument("--target-points", help="JSON landmarks for target neutral image as [row, col] pairs.")
    parser.add_argument("--driver-neutral-points", help="JSON landmarks for driver neutral image as [row, col] pairs.")
    parser.add_argument("--driver-expression-points", help="JSON landmarks for driver expression image as [row, col] pairs.")
    parser.add_argument("--target-box", help="JSON face box for target neutral image as [row0, col0, row1, col1].")
    parser.add_argument("--driver-neutral-box", help="JSON face box for driver neutral image.")
    parser.add_argument("--driver-expression-box", help="JSON face box for driver expression image.")
    parser.add_argument("--no-face-boxes", action="store_true", help="Skip face-box normalization and use raw image coordinates.")
    parser.add_argument("--interactive", action="store_true", help="Click landmarks manually instead of loading JSON files.")
    parser.add_argument(
        "--reuse-target-as-driver-neutral",
        action="store_true",
        help="Use the target image and landmarks as the driver neutral state, so only two images need to be clicked.",
    )
    parser.add_argument("--full-image-warp", action="store_true", help="Disable face-region blending and keep the full TPS warp.")
    parser.add_argument("--max-display-width", type=int, default=1000, help="Largest manual-click window width.")
    parser.add_argument("--max-display-height", type=int, default=750, help="Largest manual-click window height.")
    parser.add_argument("--strength", type=float, default=1.0, help="Expression scale. Try 0.5 for subtle or 1.5 for stronger.")
    parser.add_argument("--output-dir", default="morphing-applications/application3/outputs")
    parser.add_argument("--save-clicked-prefix", help="Prefix for saving manually clicked landmark JSON files.")
    return parser.parse_args()


def main():
    args = parse_args()

    target_neutral = read_image(args.target_neutral)
    driver_neutral_original = read_image(args.driver_neutral)
    driver_expression_original = read_image(args.driver_expression)
    driver_neutral = resize_like(driver_neutral_original, target_neutral)
    driver_expression = resize_like(driver_expression_original, target_neutral)
    target_box = None
    driver_neutral_box = None
    driver_expression_box = None

    if args.interactive:
        print("Click the same semantic landmarks in the same order for the prompted images.")
        print("Recommended points: eyes, brows, nose, mouth corners, lip contour, jaw/chin. Press Esc when done.")
        max_display_size = (args.max_display_width, args.max_display_height)
        if not args.no_face_boxes:
            target_box = collect_face_box(target_neutral, "target neutral face box", max_display_size)
            if args.reuse_target_as_driver_neutral:
                driver_neutral_box = target_box.copy()
            else:
                driver_neutral_box = collect_face_box(driver_neutral, "driver neutral face box", max_display_size)
            driver_expression_box = collect_face_box(driver_expression, "driver expression face box", max_display_size)

        target_points = collect_points(target_neutral, "target neutral landmarks", max_display_size)
        if args.reuse_target_as_driver_neutral:
            driver_neutral_points = target_points.copy()
        else:
            driver_neutral_points = collect_points(driver_neutral, "driver neutral landmarks", max_display_size)
        driver_expression_points = collect_points(driver_expression, "driver expression landmarks", max_display_size)

        if args.save_clicked_prefix:
            save_points(args.save_clicked_prefix + "_target_neutral.json", target_points)
            save_points(args.save_clicked_prefix + "_driver_neutral.json", driver_neutral_points)
            save_points(args.save_clicked_prefix + "_driver_expression.json", driver_expression_points)
            if not args.no_face_boxes:
                save_box(args.save_clicked_prefix + "_target_box.json", target_box)
                save_box(args.save_clicked_prefix + "_driver_neutral_box.json", driver_neutral_box)
                save_box(args.save_clicked_prefix + "_driver_expression_box.json", driver_expression_box)
    else:
        required = [args.target_points, args.driver_expression_points]
        if not args.reuse_target_as_driver_neutral:
            required.append(args.driver_neutral_points)
        if not args.no_face_boxes:
            required.extend([args.target_box, args.driver_expression_box])
            if not args.reuse_target_as_driver_neutral:
                required.append(args.driver_neutral_box)
        if any(path is None for path in required):
            raise ValueError("Provide the needed point JSON files, or use --interactive.")
        target_points = load_points(args.target_points)
        if args.reuse_target_as_driver_neutral:
            driver_neutral_points = target_points.copy()
        else:
            driver_neutral_points = scale_points(
                load_points(args.driver_neutral_points),
                driver_neutral_original.shape,
                target_neutral.shape,
            )
        driver_expression_points = scale_points(
            load_points(args.driver_expression_points),
            driver_expression_original.shape,
            target_neutral.shape,
        )
        if not args.no_face_boxes:
            target_box = load_box(args.target_box)
            if args.reuse_target_as_driver_neutral:
                driver_neutral_box = target_box.copy()
            else:
                driver_neutral_box = scale_box(
                    load_box(args.driver_neutral_box),
                    driver_neutral_original.shape,
                    target_neutral.shape,
                )
            driver_expression_box = scale_box(
                load_box(args.driver_expression_box),
                driver_expression_original.shape,
                target_neutral.shape,
            )

    if args.no_face_boxes:
        transferred, full_warp, target_expression_points = transfer_expression(
            target_neutral,
            target_points,
            driver_neutral_points,
            driver_expression_points,
            strength=args.strength,
            face_only=not args.full_image_warp,
        )
    else:
        transferred, full_warp, target_expression_points = transfer_expression_with_boxes(
            target_neutral,
            target_points,
            target_box,
            driver_neutral_points,
            driver_neutral_box,
            driver_expression_points,
            driver_expression_box,
            strength=args.strength,
            face_only=not args.full_image_warp,
        )
    print_motion_stats(target_points, target_expression_points)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    transferred_path = output_dir / "expression_transfer.jpg"
    full_warp_path = output_dir / "expression_transfer_full_warp.jpg"
    arrows_path = output_dir / "expression_motion.jpg"
    difference_path = output_dir / "expression_transfer_difference.jpg"
    comparison_path = output_dir / "expression_transfer_comparison.jpg"

    arrows = draw_landmark_arrows(target_neutral, target_points, target_expression_points)
    difference = make_difference_view(target_neutral, transferred)
    comparison = make_comparison(target_neutral, transferred, arrows)

    cv2.imwrite(str(transferred_path), transferred)
    cv2.imwrite(str(full_warp_path), full_warp)
    cv2.imwrite(str(arrows_path), arrows)
    cv2.imwrite(str(difference_path), difference)
    cv2.imwrite(str(comparison_path), comparison)

    print(f"Saved transferred expression: {transferred_path}")
    print(f"Saved full TPS warp: {full_warp_path}")
    print(f"Saved landmark motion view: {arrows_path}")
    print(f"Saved amplified difference view: {difference_path}")
    print(f"Saved comparison figure: {comparison_path}")


if __name__ == "__main__":
    main()
