<strong>Sample ouput:</strong>

<!-- <img width="300" height="300" alt="image" src="https://github.com/user-attachments/assets/3207051d-6e26-4a34-b652-da9665d8486f" /> -->
<img width="300" height="300" alt="output" src="https://github.com/user-attachments/assets/ffa70be3-dd75-46e5-9d0f-87322feb007c" />
<!-- <img width="610" height="612" alt="image" src="https://github.com/user-attachments/assets/3207051d-6e26-4a34-b652-da9665d8486f" />
<img width="610" height="612" alt="output" src="https://github.com/user-attachments/assets/ffa70be3-dd75-46e5-9d0f-87322feb007c" /> -->
<!-- <img width="410" height="412" alt="image" src="https://github.com/user-attachments/assets/3207051d-6e26-4a34-b652-da9665d8486f" />
<img width="410" height="412" alt="output" src="https://github.com/user-attachments/assets/ffa70be3-dd75-46e5-9d0f-87322feb007c" /> -->

---
<p>Image morphing can be defined as a technique which constructs the sequence of images
depicting the transition between them. The method that is used in this project involves using
Delaunay Triangulation and Affine transformation.</p>
<p>Firstly the images are divided into several parts by selecting different points on it. These points
on the image are called control points. The control points are used in order to apply the Delaunay
triangulation as well as the Affine transformation on the images on them. The details of the
methods are explained in the Algorithm section.</p>
<p>Morphing is mainly employed in the field of animations and special effects. In the present day
there exist many software like after effects, nuke etc. These software can also be used by people
who don’t know coding.</p>
# Instructions to use the code

This file contains the steps on how to execute the file.

<strong>Step-1</strong> Open the command line or terminal and enter the following -
```text
$python3 main.py img1.png img2.png
```
here img1 refers to the source image and img2 refers to the destination image.

<strong>Step-2</strong> Enter the control points on img1 using mouse click and press escape after entering all points. Do the same for img2 but the order of points should remain same.

The program now automatically adds boundary anchor points around the image border (corners plus quarter-edge anchors), so you only need to click the meaningful feature points manually.

After doing so the system will display as well as save the triangulated images.

<strong>Step-3</strong> Enter the number of intermediate images you want to see (This number should exclude the source and destination image as they are already taken care of).

Before entering that number, the program now asks you to choose a morphing method:
```text
affine-linear
affine-laplacian
tps-linear
tps-laplacian
```
Use the `tps-*` options for Thin Plate Spline based advanced warping.

The code will take some time to create and save the desired number of intermediates. We have directly saved the images to save the time.

<<<<<<< HEAD
## Multi Image Morphing

<Strong> sequential image morphing<Strong>  
this involves morphing the first image to the second, the second to the third and so on.  

<Strong> image averaging <Strong>
this involves finding the average morph posistion between all of the images, and averaging the images together.


```text
to use this capability add '--multi-image {directory of images}' to the command line. the program will ask you to manually pick your triangulation points, unless you have picked them in a previous iteration, in that case you can add the flag '--multi-image-trig saved'.
  
the program defaults to the sequential image morphing and will ask you how many frames you would like to generate between images, but you can add the flag '--multi-image-proccess avg' to apply image average morphing.

```

=======
>>>>>>> e069bfb4052234059e49ad9b4c6ee16060d71f9c
<strong>Step-4</strong> Open the command line or terminal and enter the following to generate mp4 video or gif with all the intermediate images generated in step-3:


## install ffmpeg
```text
$sudo apt update
$sudo apt install ffmpeg
$ffmpeg -version
```

## generate mp4 or gif
```text
$ffmpeg -framerate 15 -i generated-images/linear-dissolve/inter_%d.jpg generated-images/linear-dissolve/output.gif
$ffmpeg -framerate 15 -i generated-images/linear-dissolve/inter_%d.jpg generated-images/linear-dissolve/output.mp4

$ffmpeg -framerate 15 -i generated-images/laplacian-pyramid-blending/inter_%d.jpg generated-images/laplacian-pyramid-blending/output.gif
$ffmpeg -framerate 15 -i generated-images/laplacian-pyramid-blending/inter_%d.jpg generated-images/laplacian-pyramid-blending/output.mp4

$ffmpeg -framerate 15 -i generated-images/tps-linear-dissolve/inter_%d.jpg generated-images/tps-linear-dissolve/output.gif
$ffmpeg -framerate 15 -i generated-images/tps-linear-dissolve/inter_%d.jpg generated-images/tps-linear-dissolve/output.mp4

$ffmpeg -framerate 15 -i generated-images/tps-laplacian-pyramid-blending/inter_%d.jpg generated-images/tps-laplacian-pyramid-blending/output.gif
$ffmpeg -framerate 15 -i generated-images/tps-laplacian-pyramid-blending/inter_%d.jpg generated-images/tps-laplacian-pyramid-blending/output.mp4
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
│        ├── application3
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
│        ├── laplacian-pyramid-blending
│        │        ├── inter_1.jpg
│        │        ├── inter_2.jpg
│        │        ├── ..........
│        │        ├── inter_100.jpg
│        │        ├── output.gif
│        │        └── output.mp4
│        └── linear-dissolve
│                 ├── inter_1.jpg
│                 ├── inter_2.jpg
│                 ├── ..........
│                 ├── inter_100.jpg
│                 ├── output.gif
│                 └── output.mp4
│
├── generated-images-multi-inputs   # Multiple input images case
│   ├── inter_1.jpg
│   ├── inter_2.jpg
│   ├── ..........
│   ├── output.gif
│   └── output.mp4
│
├── main.py                         # This is the entrance Python file
│
├── input-images                    # Directory for two input images
│   ├── img1.png 
│   └── img2.png
│
├── morph                           # Morphing related source code
│   ├── blend.py
│   ├── correspondences.py
│   ├── triangulation.py
│   └── warp.py
│
├── multi-input-images              # Directory for multiple input images, which will be used to generate multiple continuous morphing effects
│   ├── multi-image1.png
│   ├── multi-image2.png
│   ├── multi-image3.png
│   └── .........
│
├── Report.pdf                      # Document
│
└── README.md

```

