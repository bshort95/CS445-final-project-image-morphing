import argparse
from pathlib import Path

import cv2
import numpy as np

from morph.correspondences import (
    boundary_anchors,
    get_automatic_face_points,
    get_manual_points,
    load_correspondences,
    remove_duplicate_correspondences,
    save_correspondences,
)
from morph.evaluation import evaluate_manual_vs_auto
from morph.triangulation import triangulate_correspondences
from morph.warp import (
    warp_image_affine_transform_with_laplacian_pyrimid_blending,
    warp_image_affine_transform_with_linear_dissolve,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Generate image morphs from manual or automatic correspondences.")
    parser.add_argument("image1", help="Source image filename in input-images/ or an explicit path.")
    parser.add_argument("image2", help="Destination image filename in input-images/ or an explicit path.")
    parser.add_argument(
        "--correspondence",
        choices=["manual", "auto", "compare"],
        default="manual",
        help="Correspondence source. Default preserves the original manual-click workflow.",
    )
    parser.add_argument("--frames", type=int, help="Number of intermediate frames to generate.")
    parser.add_argument(
        "--total-frames",
        type=int,
        help="Total output frames including endpoints, so inter_1 is source and inter_N is destination.",
    )
    parser.add_argument("--blend", choices=["linear", "laplacian"], default="laplacian")
    parser.add_argument("--no-display", action="store_true", help="Do not open OpenCV UI windows.")
    parser.add_argument(
        "--save-correspondences",
        nargs="?",
        const="generated-images/correspondences.json",
        help="Save the selected correspondences to JSON.",
    )
    parser.add_argument("--manual-correspondences", help="JSON file with saved manual correspondences.")
    parser.add_argument("--auto-correspondences", help="JSON file with saved automatic correspondences.")
    parser.add_argument("--output-dir", help="Override the generated frame output folder.")
    parser.add_argument(
        "--evaluation-only",
        action="store_true",
        help="In compare mode, reuse existing manual/auto frame folders instead of regenerating frames.",
    )
    parser.add_argument("--manual-frames-dir", help="Existing manual frame folder for --evaluation-only.")
    parser.add_argument("--auto-frames-dir", help="Existing automatic frame folder for --evaluation-only.")
    parser.add_argument(
        "--evaluation-dir",
        default="evaluation-results/manual-vs-auto",
        help="Output directory for compare-mode metrics and figures.",
    )
    return parser.parse_args()


def load_image(image_arg):
    candidates = [Path("input-images") / image_arg, Path(image_arg)]
    for path in candidates:
        if path.exists():
            image = cv2.imread(str(path))
            if image is None:
                raise ValueError(f"Unable to read image: {path}")
            return image, path
    raise FileNotFoundError(f"Could not find {image_arg} in input-images/ or as a direct path.")


def collect_points(window, image, color):
    points = []
    display = image.copy()

    def callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            cv2.circle(display, (x, y), 2, color, -1)
            points.append((y, x))

    cv2.namedWindow(window)
    cv2.setMouseCallback(window, callback)
    while True:
        cv2.imshow(window, display)
        if cv2.waitKey(20) == 27:
            break
    cv2.destroyWindow(window)
    return np.array(points, dtype=np.float32)


def collect_manual_correspondences(img1, img2, no_display=False):
    if no_display:
        print("No display is enabled; using boundary-anchor manual baseline.")
        return get_manual_points(img1, img2)

    print("Click source control points, then press Esc.")
    points1 = collect_points("image1", img1, (0, 0, 255))
    print("Click destination control points in the same order, then press Esc.")
    points2 = collect_points("image2", img2, (255, 0, 0))

    if len(points1) != len(points2):
        raise ValueError(
            f"Manual correspondence count mismatch: source has {len(points1)}, destination has {len(points2)}."
        )
    if len(points1) < 3:
        raise ValueError("At least three manual correspondences are required.")

    points1 = np.vstack([points1, boundary_anchors(img1.shape)])
    points2 = np.vstack([points2, boundary_anchors(img2.shape)])
    return remove_duplicate_correspondences(points1, points2)


def draw_delaunay(img, triangle_list, color):
    canvas = img.copy()
    normalized = []
    for triangle in triangle_list:
        tri = [tuple(map(int, point)) for point in triangle]
        pt1, pt2, pt3 = tri
        cv2.line(canvas, (pt1[1], pt1[0]), (pt2[1], pt2[0]), color, 1)
        cv2.line(canvas, (pt2[1], pt2[0]), (pt3[1], pt3[0]), color, 1)
        cv2.line(canvas, (pt3[1], pt3[0]), (pt1[1], pt1[0]), color, 1)
        normalized.append(tri)
    return canvas, normalized


def show_triangulated(img1, img2, triangles1, triangles2, no_display=False):
    Path("Triangulated Images").mkdir(parents=True, exist_ok=True)
    src_display, tri1 = draw_delaunay(img1, triangles1, (255, 0, 0))
    dest_display, tri2 = draw_delaunay(img2, triangles2, (0, 255, 255))
    cv2.imwrite("Triangulated Images/Triangulated Image_src.jpg", src_display)
    cv2.imwrite("Triangulated Images/Triangulated Image_dest.jpg", dest_display)

    if not no_display:
        cv2.imshow("src", src_display)
        cv2.imshow("dest", dest_display)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    return tri1, tri2


def triangulate(points1, points2, prefer_scipy=False):
    method = "scipy" if prefer_scipy or len(points1) > 25 else "custom"
    return triangulate_correspondences(points1, points2, method=method)


def get_output_dir(blend, correspondence, override=None):
    if override:
        return override
    prefix = "auto" if correspondence == "auto" else "manual"
    if blend == "linear":
        return f"generated-images/{prefix}-linear-dissolve"
    return f"generated-images/{prefix}-laplacian-pyrimid-blending"


def get_compare_output_dirs(blend, manual_override=None, auto_override=None):
    if blend == "linear":
        manual_output = "generated-images/manual-linear-dissolve"
        auto_output = "generated-images/auto-linear-dissolve"
    else:
        manual_output = "generated-images/manual-laplacian-pyrimid-blending"
        auto_output = "generated-images/auto-laplacian-pyrimid-blending"
    return manual_override or manual_output, auto_override or auto_output


def existing_frame_paths(frame_dir, frame_count):
    paths = [Path(frame_dir) / f"inter_{idx}.jpg" for idx in range(1, frame_count + 1)]
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        preview = ", ".join(missing[:3])
        raise FileNotFoundError(f"Missing generated frame(s): {preview}")
    return paths


def run_warp(frames, img1, img2, triangles1, triangles2, blend, output_dir, include_endpoints=False):
    if blend == "linear":
        return warp_image_affine_transform_with_linear_dissolve(
            frames, img1, img2, triangles1, triangles2, output_dir=output_dir, include_endpoints=include_endpoints
        )
    return warp_image_affine_transform_with_laplacian_pyrimid_blending(
        frames, img1, img2, triangles1, triangles2, output_dir=output_dir, include_endpoints=include_endpoints
    )


def resolve_frame_request(args):
    if args.frames is not None and args.total_frames is not None:
        raise ValueError("Use either --frames for intermediate-only output or --total-frames for endpoint-inclusive output.")
    if args.total_frames is not None:
        if args.total_frames < 2:
            raise ValueError("--total-frames must be at least 2.")
        return args.total_frames, True
    if args.frames is not None:
        if args.frames < 1:
            raise ValueError("--frames must be at least 1.")
        return args.frames, False
    return int(input("Enter number of intermediate you want ")), False


def get_auto_correspondences(args, img1, img2):
    if args.auto_correspondences:
        return load_correspondences(args.auto_correspondences)
    return get_automatic_face_points(img1, img2)


def get_manual_correspondences(args, img1, img2):
    if args.manual_correspondences:
        return load_correspondences(args.manual_correspondences)
    return collect_manual_correspondences(img1, img2, no_display=args.no_display)


def run_single_mode(args, img1, img2):
    frames, include_endpoints = resolve_frame_request(args)
    if args.correspondence == "auto":
        points1, points2 = get_auto_correspondences(args, img1, img2)
        prefer_scipy = True
    else:
        points1, points2 = get_manual_correspondences(args, img1, img2)
        prefer_scipy = len(points1) > 25

    if args.save_correspondences:
        save_correspondences(
            args.save_correspondences,
            points1,
            points2,
            metadata={
                "mode": args.correspondence,
                "blend": args.blend,
                "frames": frames,
                "include_endpoints": include_endpoints,
            },
        )

    triangles1, triangles2 = triangulate(points1, points2, prefer_scipy=prefer_scipy)
    tri1, tri2 = show_triangulated(img1, img2, triangles1, triangles2, no_display=args.no_display)
    output_dir = get_output_dir(args.blend, args.correspondence, args.output_dir)
    frame_paths = run_warp(frames, img1, img2, tri1, tri2, args.blend, output_dir, include_endpoints)
    print(f"Generated {len(frame_paths)} frames in {output_dir}")


def run_compare_mode(args, img1, img2):
    frames, include_endpoints = resolve_frame_request(args)
    manual_points1, manual_points2 = get_manual_correspondences(args, img1, img2)
    auto_points1, auto_points2 = get_auto_correspondences(args, img1, img2)

    if args.save_correspondences:
        save_correspondences(
            Path(args.save_correspondences).with_name("manual_correspondences.json"),
            manual_points1,
            manual_points2,
            metadata={"mode": "manual", "blend": args.blend, "frames": frames, "include_endpoints": include_endpoints},
        )
        save_correspondences(
            Path(args.save_correspondences).with_name("auto_correspondences.json"),
            auto_points1,
            auto_points2,
            metadata={"mode": "auto", "blend": args.blend, "frames": frames, "include_endpoints": include_endpoints},
        )

    manual_triangles = triangulate(manual_points1, manual_points2, prefer_scipy=len(manual_points1) > 25)
    auto_triangles = triangulate(auto_points1, auto_points2, prefer_scipy=True)

    manual_output, auto_output = get_compare_output_dirs(args.blend, args.manual_frames_dir, args.auto_frames_dir)

    if args.evaluation_only:
        manual_frames = existing_frame_paths(manual_output, frames)
        auto_frames = existing_frame_paths(auto_output, frames)
    else:
        manual_frames = run_warp(
            frames,
            img1,
            img2,
            manual_triangles[0],
            manual_triangles[1],
            args.blend,
            manual_output,
            include_endpoints,
        )
        auto_frames = run_warp(
            frames,
            img1,
            img2,
            auto_triangles[0],
            auto_triangles[1],
            args.blend,
            auto_output,
            include_endpoints,
        )

    metrics_path = evaluate_manual_vs_auto(
        img1,
        img2,
        manual_points1,
        manual_points2,
        auto_points1,
        auto_points2,
        manual_triangles,
        auto_triangles,
        manual_frames,
        auto_frames,
        output_dir=args.evaluation_dir,
        include_endpoints=include_endpoints,
        blend_name=args.blend,
    )
    print(f"Evaluation metrics saved to {metrics_path}")


def main():
    args = parse_args()
    img1, _ = load_image(args.image1)
    img2, _ = load_image(args.image2)
    img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

    if args.correspondence == "compare":
        run_compare_mode(args, img1, img2)
    else:
        run_single_mode(args, img1, img2)


if __name__ == "__main__":
    main()
