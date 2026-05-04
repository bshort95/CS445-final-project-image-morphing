
<h1 align="center">Image morphing application - Hybrid Image using Image Morphing</h1>

<p align="center">
  <strong>2026 Spring CS445 Final Course Project Morphing Application</strong><br>
</p>

---

<br>

## Project overview:
This application implemented paper: Hybrid Image using Image Morphing (https://dl.acm.org/doi/10.1145/2811411.2811547). 
Hybrid image refers to an image that is viewed in two different ways, depending on the distance of a viewer. This optical illusion comes from human perception of concentrating on the specific spatial frequency band information with regard to the observation distance. However, the existing hybrid image synthesis method has limited application to making diverse contents since two input images have to have similar shape and alignment for synthesis and sometimes the image is not easily perceived from certain distances. This application
uses the image morphing method to improve the limitations, based on morphing generated smooth transformation, hybrid image is created. This method can be used to create an excellent quality hybrid image without using images of similar shape or alignment, and the produced image is easily perceived at different viewing distances.
##
<br>

<br>

### Working directory:
./morphing_applications/hybrid_image_with_morphing

### 1. Command:

```text
$ python3 hybrid_morphing_main.py einstein.png monroe.png
```
   
### 2. The synthesized hybrid morphing image is under below directory:
```text
./morphing_applications/hybrid_image_with_morphing/generated-images/laplacian-pyramid-blending/output/hybrid_morph_blending_result.jpg
```

<br>


## Project Structure

```text
./morphing_applications/hybrid_image_with_morphing/
│
├── generated-images/laplacian-pyramid-blending
│    ├── hipass            # Generated hipass laplacian pyramid images
│    │    └── inter_hipass_1_level_1.jpg    
│    │    ├── ......        
│    │    ├── inter_hipass_4_level_4.jpg   
│    │    └── inter_lowpass_5_level_6.jpg
│    ├── output        # Result hybrid morphing image
│    │    └── hybrid_morph_blending_result.jpg   
│    ├── inter_1.jpg        
│    ├── inter_2.jpg        
│    ├── ......        
│    └── inter_5.jpg        
│
│── input-images
│        ├── img1.png        
│        └── img2.png
│
├── hybrid_morphing_main.py                       # This is the application main entry
│
├── Hybrid Image using Image Morphing.pdf         # Paper doc
│
├── Triangulated Images
│   ├── Triangulated Image_src.jpg            
│   └── Triangulated Image_dest.jpg      
│
├── utils       
│   └── image_utils.py     
│
├── morph                     
│   ├── blend.py
│   ├── correspondences.py
│   ├── triangulation.py
│   └── warp.py
│
└── README.md                     
```

---


<br><br>

<br><br>

---
Output hybrid morphing image:
-
<img width="1669" height="228" alt="image" src="https://github.com/user-attachments/assets/dcceca1c-8f7f-468a-a437-5c236f493b78" />
<img width="1544" height="477" alt="image" src="https://github.com/user-attachments/assets/af123077-6420-48e9-a7a6-df0ee3969feb" />
<img width="1671" height="383" alt="image" src="https://github.com/user-attachments/assets/7d8b64fa-2c5f-4f8c-a878-9b245115246f" />
 
<br>




<br><br>







