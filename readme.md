<h1 align="center">Enhanced image morphing and useful applications</h1>

<p align="center">
  <strong>2026 Spring CS445 Course Project</strong><br>
</p>

---

## Project effect samples:
<!-- <strong>Sample ouput:</strong> -->

<!-- <img width="300" height="300" alt="image" src="https://github.com/user-attachments/assets/3207051d-6e26-4a34-b652-da9665d8486f" /> -->
<img width="300" height="300" alt="output" src="https://github.com/user-attachments/assets/ffa70be3-dd75-46e5-9d0f-87322feb007c" />
<!-- <img width="610" height="612" alt="image" src="https://github.com/user-attachments/assets/3207051d-6e26-4a34-b652-da9665d8486f" />
<img width="610" height="612" alt="output" src="https://github.com/user-attachments/assets/ffa70be3-dd75-46e5-9d0f-87322feb007c" /> -->
<!-- <img width="410" height="412" alt="image" src="https://github.com/user-attachments/assets/3207051d-6e26-4a34-b652-da9665d8486f" />
<img width="410" height="412" alt="output" src="https://github.com/user-attachments/assets/ffa70be3-dd75-46e5-9d0f-87322feb007c" /> -->
<!-- <img width="300" height="300" alt="output" src="https://github.com/user-attachments/assets/e0c62f97-3173-4ed5-88bd-2731ee747aeb" /> -->
<!-- <img width="300" height="300" alt="output-5M" src="https://github.com/user-attachments/assets/487bf053-9f43-4db9-a5da-ebc20de29554" /> -->
<img width="300" height="300" alt="output-5m" src="https://github.com/user-attachments/assets/842790cf-af68-4106-8f48-eee77d2ee2d7" />

---
## Project overview:
<p>Image morphing is a digital image processing technique that creates a smooth and continuous transformation from one image to another. Unlike simple crossfading (which only blends pixel intensities), morphing combines geometric warping and color interpolation to produce a visually coherent transition where shapes, structures, and textures appear to evolve naturally over time. The basic techniques used in image morphing are: Linear cross-dissolve blending, Delaunay Triangulation, and Affine transformation. In this project, we will explore the advanced techniques which can enrich and enhance image morphing functionalities.</p>
<p>Firstly, the images are divided into several parts by selecting different points on them. These points
on the image are called control points. The control points are used to apply the Delaunay
triangulation as well as the geometric transformation to the images. </p>
<p>Morphing is primarily used in animation and special effects. In the present day,
there exist many software programs like After Effects, Nuke, etc. This software can also be used by people
who don’t know coding.</p>

## We focus on:
<p> We focus on advanced techniques that can enhance the morphing effect. For example, advanced geometric transformation, advanced image intensity blending, automatic landmark selecting and triangulation, supporting multiple input images bulk morphing, etc.</p>

## Implementation:

|   🔷 Basic image morphing       |          🔷 Enhanced image morphing                           |
|---------------------------------|---------------------------------------------------------------|
| Linear cross-dissolve blending  | Multi-band Gaussian-Laplacian pyramid blending                |
| Affine transformation           | Advanced TPS (Thin Plate Splines) transformation              |
| Manual control points selection | Automatic feature point/landmark detection and triangulation  |
| Two image morphing              | Support multi-input images' bulk morphing                     |


## Image morphing applications:
1. [Hybrid image using image morphing](https://github.com/johnlee2898-2/CS445-final-project-image-morphing/tree/main/morphing_applications/hybrid_image_with_morphing)
2. [Multi-image face averaging](https://github.com/johnlee2898-2/CS445-final-project-image-morphing/tree/main/morphing_applications/multi_img_processing)
3. [Expression transfer](https://github.com/johnlee2898-2/CS445-final-project-image-morphing/tree/main/morphing_applications/application3)
4. Application 4

---

## Instructions to use the code

This file contains the steps on how to execute the file.

### Main command options

`main.py` supports these options for the two-image morphing flow:

| Option | Values | Description |
|--------|--------|-------------|
| `--correspondence` | `manual`, `auto`, `compare` | Choose manual point clicking, automatic face landmark correspondences, or manual-vs-auto evaluation. |
| `--transform` | `affine`, `tps` | Choose affine triangle warping or Thin Plate Spline warping. |
| `--blend` | `linear`, `laplacian` | Choose linear cross-dissolve or Gaussian-Laplacian pyramid blending. |
| `--frames` | integer | Number of intermediate frames to generate, excluding the source and destination images. |
| `--total-frames` | integer | Total number of output frames, including source and destination endpoints. |
| `--no-display` | flag | Save outputs without opening OpenCV display windows. Useful for automatic runs. |
| `--save-correspondences` | optional path | Save the selected correspondence points to JSON. |

Note: TPS mode uses `--frames`. Do not use `--total-frames` with `--transform tps`.

<strong>Step-1</strong> Open the command line or terminal and enter the following -
```text
$ python3 main.py img1.png img2.png
```
here img1 refers to the source image and img2 refers to the destination image.

<strong>Step-2</strong> Enter the control points on img1 using mouse click and press escape after entering all points. Do the same for img2 but the order of points should remain same.

The program now automatically adds boundary anchor points around the image border (corners plus quarter-edge anchors), so you only need to click the meaningful feature points manually.

After doing so the system will display as well as save the triangulated images.

<strong>Step-3</strong> Enter the number of intermediate images you want to see, or pass it directly with `--frames`.

The morphing method is selected from the command line. Use `--transform affine` or `--transform tps`, and use `--blend linear` or `--blend laplacian`.

The code will take some time to create and save the desired number of intermediates. We have directly saved the images to save the time.

### Automatic Correspondence Examples

Automatic correspondence uses face landmarks, so it works best when each input image contains a clear face.

```text
$ python3 main.py img1.png img2.png --correspondence auto --transform affine --blend linear --frames 30 --no-display
$ python3 main.py img1.png img2.png --correspondence auto --transform affine --blend laplacian --frames 30 --no-display
```

To save the automatically detected points and reuse them later:

```text
$ python3 main.py img1.png img2.png --correspondence auto --save-correspondences generated-images/auto_correspondences.json --frames 30 --no-display
$ python3 main.py img1.png img2.png --correspondence auto --auto-correspondences generated-images/auto_correspondences.json --frames 30 --no-display
```

### TPS Transformation Examples

Thin Plate Spline transformation is selected with `--transform tps`. It can be combined with manual or automatic correspondences and either blending method.

```text
$ python3 main.py img1.png img2.png --correspondence manual --transform tps --blend linear --frames 30
$ python3 main.py img1.png img2.png --correspondence manual --transform tps --blend laplacian --frames 30
$ python3 main.py img1.png img2.png --correspondence auto --transform tps --blend laplacian --frames 30 --no-display
```

Output folders:

```text
generated-images/manual-linear-dissolve/
generated-images/manual-laplacian-pyramid-blending/
generated-images/auto-linear-dissolve/
generated-images/auto-laplacian-pyramid-blending/
generated-images/tps-linear-dissolve/
generated-images/tps-laplacian-pyramid-blending/
```

Note: `--multi-image ""` is not needed for normal two-image morphing. Leave `--multi-image` out unless you want to run the multi-image feature.

The command below is the corrected version of the auto-correspondence plus Laplacian example. It uses the default affine transform and runs the two-image flow:

```text
$ python3 main.py img1.png img2.png --blend laplacian --correspondence auto --frames 30 --no-display
```


## Multi Image Morphing

<Strong> sequential image morphing<Strong>  
this involves morphing the first image to the second, the second to the third and so on.  

<Strong> image averaging <Strong>
this involves finding the average morph posistion between all of the images, and averaging the images together.


```text
to use this capability add '--multi-image {directory of images}' to the command line. the program will ask you to manually pick your triangulation points, unless you have picked them in a previous iteration, in that case you can add the flag '--multi-image-trigs saved'.
  
the program defaults to the sequential image morphing and will ask you how many frames you would like to generate between images, but you can add the flag '--multi-image-proccess avg' to apply image average morphing.

```
```text
$ python3 main.py img1.png img8.png --multi-image ./multi-input-images/ --blend linear --correspondence manual --frames 10
$ python3 main.py img1.png img8.png --multi-image ./multi-input-images/ --blend laplacian --correspondence manual --frames 10
```

### Multi-Image TPS Demo

Use `--transform tps` to run Thin Plate Spline warping through the whole multi-image sequence. It can be combined with `--blend linear` or `--blend laplacian`. Manual mode uses the saved or newly clicked control points for each image.

```text
$ python3 main.py img1.png img8.png --multi-image ./multi-input-images/ --correspondence manual --transform tps --blend linear --frames 10
$ python3 main.py img1.png img8.png --multi-image ./multi-input-images/ --correspondence manual --transform tps --blend laplacian --frames 10
```

For an overall demo that combines multi-image morphing, automatic correspondence, TPS transformation, and Laplacian pyramid blending:

```text
$ python3 main.py img1.png img8.png --multi-image ./multi-input-images/ --correspondence auto --transform tps --blend laplacian --frames 10 --no-display
```

Output folders:

```text
generated-images/multi-input-linear-dissolve/
generated-images/multi-input-laplacian-pyramid-blending/
generated-images/multi-input-tps-linear-dissolve/
generated-images/multi-input-tps-laplacian-pyramid-blending/
```

<strong>Step-4</strong> Open the command line or terminal and enter the following to generate mp4 video or gif with all the intermediate images generated in step-3:


## install ffmpeg
```text
$ sudo apt update
$ sudo apt install ffmpeg
$ ffmpeg -version
```

## generate mp4 or gif
```text
$ ffmpeg -framerate 15 -start_number 1 -i generated-images/manual-linear-dissolve/inter_%d.jpg generated-images/manual-linear-dissolve/output.gif
$ ffmpeg -framerate 15 -start_number 1 -i generated-images/manual-linear-dissolve/inter_%d.jpg generated-images/manual-linear-dissolve/output.mp4

$ ffmpeg -framerate 15 -start_number 1 -i generated-images/manual-laplacian-pyramid-blending/inter_%d.jpg generated-images/manual-laplacian-pyramid-blending/output.gif
$ ffmpeg -framerate 15 -start_number 1 -i generated-images/manual-laplacian-pyramid-blending/inter_%d.jpg generated-images/manual-laplacian-pyramid-blending/output.mp4

$ ffmpeg -framerate 15 -start_number 1 -i generated-images/auto-linear-dissolve/inter_%d.jpg generated-images/auto-linear-dissolve/output.gif
$ ffmpeg -framerate 15 -start_number 1 -i generated-images/auto-linear-dissolve/inter_%d.jpg generated-images/auto-linear-dissolve/output.mp4

$ ffmpeg -framerate 15 -start_number 1 -i generated-images/auto-laplacian-pyramid-blending/inter_%d.jpg generated-images/auto-laplacian-pyramid-blending/output.gif
$ ffmpeg -framerate 15 -start_number 1 -i generated-images/auto-laplacian-pyramid-blending/inter_%d.jpg generated-images/auto-laplacian-pyramid-blending/output.mp4

$ ffmpeg -framerate 15 -start_number 1 -i generated-images/tps-linear-dissolve/inter_%d.jpg generated-images/tps-linear-dissolve/output.gif
$ ffmpeg -framerate 15 -start_number 1 -i generated-images/tps-linear-dissolve/inter_%d.jpg generated-images/tps-linear-dissolve/output.mp4

$ ffmpeg -framerate 15 -start_number 1 -i generated-images/tps-laplacian-pyramid-blending/inter_%d.jpg generated-images/tps-laplacian-pyramid-blending/output.gif
$ ffmpeg -framerate 15 -start_number 1 -i generated-images/tps-laplacian-pyramid-blending/inter_%d.jpg generated-images/tps-laplacian-pyramid-blending/output.mp4

$ ffmpeg -framerate 15 -i generated-images/multi-input-laplacian-pyramid-blending/inter_%d.jpg generated-images/multi-input-laplacian-pyramid-blending/output.gif
$ ffmpeg -framerate 15 -i generated-images/multi-input-laplacian-pyramid-blending/inter_%d.jpg generated-images/multi-input-laplacian-pyramid-blending/output.mp4
$ ffmpeg -framerate 15 -i generated-images/multi-input-linear-dissolve/inter_%d.jpg generated-images/multi-input-linear-dissolve/output.gif
$ ffmpeg -framerate 15 -i generated-images/multi-input-linear-dissolve/inter_%d.jpg generated-images/multi-input-linear-dissolve/output.mp4
$ ffmpeg -framerate 15 -i generated-images/multi-input-tps-linear-dissolve/inter_%d.jpg generated-images/multi-input-tps-linear-dissolve/output.gif
$ ffmpeg -framerate 15 -i generated-images/multi-input-tps-linear-dissolve/inter_%d.jpg generated-images/multi-input-tps-linear-dissolve/output.mp4
$ ffmpeg -framerate 15 -i generated-images/multi-input-tps-laplacian-pyramid-blending/inter_%d.jpg generated-images/multi-input-tps-laplacian-pyramid-blending/output.gif
$ ffmpeg -framerate 15 -i generated-images/multi-input-tps-laplacian-pyramid-blending/inter_%d.jpg generated-images/multi-input-tps-laplacian-pyramid-blending/output.mp4
```


---
<strong>Note: Please follow the project structure to add more files </strong>
## Project Structure

```text
CS445-final-project-image-morphing/

│── morphing-applications           # Directory for all morphing useful applications
│        ├── hybrid_image_with_morphing
│        ├── multi_img_processing   # average and sequential multi image processing
│        |        ├── multi-input-generated-imgs
|        |        ├── multi-input-triangulated-imgs
|        |        ├── trig-files
|        |        └── utils.py
│        ├── expression_transfer
│        └── application4
│
├── utils
│    └── image_utils.py             # Directory for all utils files
│
│── Triangulated Images             # Directory for generated triangulated images
│        ├── Triangulated Image_src.jpg
│        └── Triangulated Image_dest.jpg
│
├── generated-images                # Directory saving all generated intermediate morphing images and generated MP4 and GIF files
│        ├── manual-laplacian-pyramid-blending         # Laplacian pyramid blending
│        │        ├── inter_1.jpg
│        │        ├── inter_2.jpg
│        │        ├── ..........
│        │        ├── inter_100.jpg
│        │        ├── output.gif
│        │        └── output.mp4
│        ├── manual-linear-dissolve                    # Linear cross-dissolve blending
│        │        ├── inter_1.jpg
│        │        ├── inter_2.jpg
│        │        ├── ..........
│        │        ├── inter_100.jpg
│        │        ├── output.gif
│        │        └── output.mp4
│        ├── auto-laplacian-pyramid-blending            # Automatic correspondence
│        ├── auto-linear-dissolve
│        ├── multi-input-laplacian-pyramid-blending     # Multiple input images case
│        ├── multi-input-linear-dissolve
│        ├── multi-input-tps-linear-dissolve            # Multiple input images with TPS
│        ├── multi-input-tps-laplacian-pyramid-blending # Multiple input images with TPS and Laplacian blending
│        ├── tps-laplacian-pyramid-blending             # Tps transformation
│        └── tps-linear-dissolve
|
│
├── evaluation-results
│        ├── manual-vs-auto
│        └── matplotlib-cache
│
├── main.py                         # This is the entrance Python file
│
├── input-images                    # Directory for two input images
│       ├── img1.png 
│       └── img2.png
│
├── morph                           # Morphing related source code
│       ├── blend.py
│       ├── correspondences.py
│       ├── triangulation.py
│       ├── evaluation.py
│       ├── tps.py
│       └── warp.py
│
├── multi-input-images              # Directory for multiple input images, which will be used to generate multiple continuous morphing effects
│       ├── multi-image1.png
│       ├── multi-image2.png
│       ├── multi-image3.png
│       └── .........
│
├── requirements.txt                # Document
│
└── README.md

```

