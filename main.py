import argparse
from pathlib import Path
import copy
import cv2
import numpy as np

from morphing_applications.multi_img_processing.utils import (
    create_avg_img, 
    get_multi_input_images,
    write_trig_files, 
    read_trig_files,
    show_triangulated_for_muliple_imgs,
    warp_image_affine_transform_multiple_imgs, 
    warp_image_affine_transform_multiple_imgs_laplacian_pyramid_blending,
    get_intermediate_triangle
)
from morph.correspondences import (
    boundary_anchors,
    detect_face_landmarks,
    get_automatic_face_points,
    get_manual_points,
    load_correspondences,
    remove_duplicate_correspondences,
    save_correspondences,
)
from morph.evaluation import evaluate_manual_vs_auto
from morph.triangulation import triangulate_correspondences
from morph.warp import (
    warp_image_affine_transform_with_laplacian_pyramid_blending,
    warp_image_affine_transform_with_linear_dissolve,
)
from morph.tps import (
    warp_image_tps_transform_multiple_imgs,
    warp_image_tps_with_laplacian_pyramid_blending,
    warp_image_tps_with_linear_dissolve,
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
    parser.add_argument(
        "--transform",
        choices=["affine", "tps"],
        default="affine",
        help="Geometric warp model. Use tps for Thin Plate Spline transformation.",
    )
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
    parser.add_argument("--multi-image", default="", help="directory where multiple imges are kept")
    parser.add_argument("--multi-image-proccess", default="seq", help = "'seq' means you want to merge the images into a sequence of morphes, while 'avg' means you want to average the photos")
    parser.add_argument("--multi-image-trigs", help="enter saved if you want to used saved coordinate from last manual point selection")
    return parser.parse_args()

from morph.triangulation import compute_delaunay

#######################################################################################################################################
# CallBackFuncForimg1 
# To get callback coordinates and draw circle at points clicked in source image which are the control points in source image 
# CallBackFuncForimg2 
# To get callback coordinates and draw circle at points clicked in destination image which are the control points in source image
# getcoord
# To get the coordinates from the user using left mouse button click and storing that values in a list. One can select as many control points along with border points but it should be greater then 3
###########################################################################################################################################

def CallBackFuncForimg1(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        cv2.circle(im1, (x,y), 1, (0, 0, 255), 2)
        coordSrc.append((y,x))

def CallBackFuncForimg2(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        cv2.circle(im2, (x,y), 1, (255, 0, 0), 2)
        coordDest.append((y,x))
        
def getcoord(window,image):
    while (True):
        cv2.imshow(window, image)
        if cv2.waitKey(20) == 27:
            break
    cv2.destroyAllWindows()


def add_default_boundary_points(coord, image_shape):
    height, width = image_shape[:2]
    row_quarters = [0, height // 4, height // 2, (3 * height) // 4, height - 1]
    col_quarters = [0, width // 4, width // 2, (3 * width) // 4, width - 1]
    boundary_points = [
        (0, col_quarters[0]),
        (0, col_quarters[1]),
        (0, col_quarters[2]),
        (0, col_quarters[3]),
        (0, col_quarters[4]),
        (row_quarters[1], 0),
        (row_quarters[2], 0),
        (row_quarters[3], 0),
        (row_quarters[1], width - 1),
        (row_quarters[2], width - 1),
        (row_quarters[3], width - 1),
        (height - 1, col_quarters[0]),
        (height - 1, col_quarters[1]),
        (height - 1, col_quarters[2]),
        (height - 1, col_quarters[3]),
        (height - 1, col_quarters[4]),
    ]

    existing = set(coord)
    for point in boundary_points:
        if point not in existing:
            coord.append(point)
            existing.add(point)
    return coord

##############################################################################
# draw_delauany(img,triangleList,delaunay_color)
# To display the valid delaunany triangle in the image.
# Arguments:
# This function takes 3 arguments as img, triangleList and delaunay_color<br>
# img - The image on which we have to draw the triangles<br>
# triangleList - The list coordinates of the valid triangles.<br>
# delauany_color - the color of the lines of the triangles.
# 
# return type: 
# returns the image having the triangle.
##############################################################################     

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


##############################################################
# showTriangulated(img1,img2)
# To display the valid delaunany triangle in the image.
# Arguments:
# This function takes 2 arguments as img1 and img2
# img1 = source image
# img2 = destination image
# return type:
# returns the image having the triangle for further process.
################################################################     

def showTriangulated(img1,img2):
    size = img1.shape
    r = (0, 0, size[1], size[0])
    
    coord = coordSrc.copy()
    
    triangleList = compute_delaunay(coord)
    
    tri1 = draw_delaunay(img1,triangleList,(255,0,0))
    
    # Matching the point p0,..,pn of the source and destination image
    tri2 = []
    for i in range(len(tri1)):
        a = []
        for j in range(len(tri1[i])):
            a.append(coordDest[coordSrc.index(tri1[i][j])])
        tri2.append(a)
        
    tri2 = draw_delaunay(img2,tri2,(0,255,255))
    
    cv2.imshow("src",img1)
    cv2.imshow("dest",img2)
    cv2.imwrite("Triangulated Images/Triangulated Image_src.jpg",img1)
    cv2.imwrite("Triangulated Images/Triangulated Image_dest.jpg",img2)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return tri1,tri2

#################################################################
# Reading of input images and resizing them to same size
# img1=cv2.imread("bush.jpg")
# img2=cv2.imread("clinton.jpg")
#################################################################


def get_output_dir(blend, correspondence, override=None):
    if override:
        return override
    prefix = "auto" if correspondence == "auto" else "manual"
    if blend == "linear":
        return f"generated-images/{prefix}-linear-dissolve"
    return f"generated-images/{prefix}-laplacian-pyramid-blending"


def get_compare_output_dirs(blend, manual_override=None, auto_override=None):
    if blend == "linear":
        manual_output = "generated-images/manual-linear-dissolve"
        auto_output = "generated-images/auto-linear-dissolve"
    else:
        manual_output = "generated-images/manual-laplacian-pyramid-blending"
        auto_output = "generated-images/auto-laplacian-pyramid-blending"
    return manual_override or manual_output, auto_override or auto_output


def collect_manual_correspondences(img1, img2, no_display=False):
    if no_display:
        return get_manual_points(img1, img2)

    global im1, im2, coordSrc, coordDest
    im1 = img1.copy()
    im2 = img2.copy()
    coordSrc = []
    coordDest = []

    cv2.namedWindow("source")
    cv2.setMouseCallback("source", CallBackFuncForimg1)
    getcoord("source", im1)
    cv2.namedWindow("destination")
    cv2.setMouseCallback("destination", CallBackFuncForimg2)
    getcoord("destination", im2)

    if len(coordSrc) != len(coordDest):
        raise ValueError("Source and destination images must have the same number of control points.")
    if len(coordSrc) < 3:
        raise ValueError("At least 3 control points are required.")

    coordSrc = add_default_boundary_points(coordSrc, img1.shape)
    coordDest = add_default_boundary_points(coordDest, img2.shape)
    print("Added default boundary anchor points (corners plus quarter-edge anchors) to both images.")
    return remove_duplicate_correspondences(coordSrc, coordDest)


def show_triangulated(img1, img2, triangles1, triangles2, no_display=False):
    tri_img1 = img1.copy()
    tri_img2 = img2.copy()
    tri1 = draw_delaunay(tri_img1, triangles1, (255, 0, 0))
    tri2 = draw_delaunay(tri_img2, triangles2, (0, 255, 255))

    output_dir = Path("Triangulated Images")
    output_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_dir / "Triangulated Image_src.jpg"), tri_img1)
    cv2.imwrite(str(output_dir / "Triangulated Image_dest.jpg"), tri_img2)

    if not no_display:
        cv2.imshow("src", tri_img1)
        cv2.imshow("dest", tri_img2)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return tri1, tri2

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
    return warp_image_affine_transform_with_laplacian_pyramid_blending(
        frames, img1, img2, triangles1, triangles2, output_dir=output_dir, include_endpoints=include_endpoints
    )


def run_tps_warp(frames, img1, img2, points1, points2, blend, output_dir, include_endpoints=False):
    if include_endpoints:
        raise ValueError("Original TPS mode supports --frames only, not --total-frames.")

    if blend == "linear":
        return warp_image_tps_with_linear_dissolve(frames, img1, img2, points1, points2, output_dir=output_dir)
    else:
        return warp_image_tps_with_laplacian_pyramid_blending(
            frames, img1, img2, points1, points2, output_dir=output_dir
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

    output_dir = get_output_dir(args.blend, args.correspondence, args.output_dir)
    if args.transform == "tps":
        if not args.output_dir:
            output_dir = (
                "generated-images/tps-linear-dissolve"
                if args.blend == "linear"
                else "generated-images/tps-laplacian-pyramid-blending"
            )
        frame_paths = run_tps_warp(frames, img1, img2, points1, points2, args.blend, output_dir, include_endpoints)
    else:
        method = "scipy" if prefer_scipy else "custom"
        triangles1, triangles2 = triangulate_correspondences(points1, points2, method=method)
        tri1, tri2 = show_triangulated(img1, img2, triangles1, triangles2, no_display=args.no_display)
        frame_paths = run_warp(frames, img1, img2, tri1, tri2, args.blend, output_dir, include_endpoints)
    print(f"Generated {len(frame_paths)} frames in {output_dir}")


def run_compare_mode(args, img1, img2):
    if args.transform == "tps":
        raise ValueError("--correspondence compare currently evaluates affine triangulation outputs; use --transform affine.")

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

    manual_triangles = triangulate_correspondences(
        manual_points1, manual_points2, method="scipy" if len(manual_points1) > 25 else "custom"
    )
    auto_triangles = triangulate_correspondences(auto_points1, auto_points2, method="scipy")

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


def load_input_image(path_or_name):
    path = Path(path_or_name)
    if not path.exists():
        path = Path("input-images") / path_or_name
    img = cv2.imread(str(path))
    if img is None:
        raise FileNotFoundError(f"Could not read image: {path_or_name}")
    return img


def get_auto_multi_correspondences(imgs):
    point_sets = []
    for idx, img in enumerate(imgs):
        points = detect_face_landmarks(img, include_boundary=True)
        point_sets.append(points)
        print(f"Detected {len(points)} automatic control points for multi-image input {idx}.")
    point_count = len(point_sets[0])
    if any(len(points) != point_count for points in point_sets):
        raise ValueError("Automatic multi-image TPS requires the same number of landmarks in every image.")
    return point_sets


def run_multi_image_mode(args):
    imgs = get_multi_input_images(args.multi_image)
    imgs_original = [img.copy() for img in imgs]

    if args.multi_image_proccess != "avg":
        frames = args.frames if args.frames is not None else int(input("how many frames between images would you like?"))
        if frames < 1:
            raise ValueError("--frames must be at least 1.")

        if args.transform == "tps":
            if args.correspondence == "auto":
                point_sets = get_auto_multi_correspondences(imgs)
            else:
                if args.multi_image_trigs != "saved":
                    write_trig_files(imgs)
                point_sets = read_trig_files()
            output_dir = args.output_dir or (
                "generated-images/multi-input-tps-linear-dissolve"
                if args.blend == "linear"
                else "generated-images/multi-input-tps-laplacian-pyramid-blending"
            )
            frame_paths = warp_image_tps_transform_multiple_imgs(
                frames, imgs_original, point_sets, output_dir=output_dir, blend=args.blend
            )
            print(f"Generated {len(frame_paths)} TPS multi-image frames in {output_dir}.")
            return

    if args.multi_image_trigs != "saved":
        write_trig_files(copy.deepcopy(imgs))

    trigs = read_trig_files()
    tris = show_triangulated_for_muliple_imgs(imgs, trigs)

    if args.multi_image_proccess == "avg":
        create_avg_img(imgs, tris)
    elif args.blend == "linear":
        warp_image_affine_transform_multiple_imgs(frames, imgs_original, tris)
    else:
        warp_image_affine_transform_multiple_imgs_laplacian_pyramid_blending(frames, imgs_original, tris)


def main():
    args = parse_args()
    if args.multi_image:
        run_multi_image_mode(args)
    else:
        img1 = load_input_image(args.image1)
        img2 = load_input_image(args.image2)
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

        if args.correspondence == "compare":
            run_compare_mode(args, img1, img2)
        else:
            run_single_mode(args, img1, img2)


if __name__ == "__main__":
    main()
