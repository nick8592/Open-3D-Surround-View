# SVM Stitching & Look-Up Tables (LUT)

## 1. The Bird's-Eye View Geometry (Z=0 Plane)
The fundamental concept of any Surround-View Monitor is the **Ground Plane Assumption**. Since the driver wants to see the surrounding parking space (the ground), the system mathematically creates a flat virtual grid exactly at `Z=0` in the ISO 8855 World Coordinate System.

In `stitching_bev.py`, we define a virtual camera looking straight down at this 2D grid covering a 10m x 10m physical area (X: -5m to +5m, Y: -5m to +5m). Because we assume the ground is flat (`Z=0`), any object that is physically *taller* than the ground (like a wall, a pole, or another car bumper) will mathematically stretch outward radially from the cameras.

## 2. Reverse Projection (World-to-Image Mapping)
A common mistake in SVM design is looping over the camera's image pixels and trying to guess where they land on the ground. Because fisheye lenses bend heavily, this "Forward Mapping" approach creates holes and broken pixels in the final image.

Instead, we use **Reverse Projection Mapping**:
1. We iterate over every single virtual 3D point on the BEV ground plane grid (`X, Y, Z=0`).
2. We feed that physical 3D point into the inverse rotation (`rvec`) and inverse translation (`tvec`) math.
3. We calculate exactly which `x` and `y` pixel on the physical camera's image sensor would be looking at that specific patch of dirt.
4. We record that specific `x, y` mapping instruction.

## 3. Stitching and Alpha Weight Blending
The Front Camera and Left Camera will both see the same physical corner of the car (e.g., coordinates `X=3.0, Y=3.0`).
If we simply cut the image in half diagonally (a Hard Seam), slight calibration errors or lighting differences would look jarring and ugly.

Instead, we apply **Radial Alpha Blending**:
Every mapped pixel calculates its physical distance from the camera's optical center. As a pixel gets further away from the lens center towards the fisheye edge, its "weight" (alpha opacity) drops smoothly from 1.0 (100% opaque) down to 0.0 (fully transparent).
When the Front and Left cameras overlap at `(X=3.0, Y=3.0)`, the renderer seamlessly averages their colors together in a gradient transition, hiding the seam.

## 4. Hardware Optimization (Look-Up Tables)
Calculating complex 3D trigonometry (sine, cosine, equidistant polynomial geometry) for 1 million pixels (1000x1000 BEV surface) 4 times over (4 cameras) is computationally too expensive for a real-time 60FPS dashboard ECU to run every frame.

### The Physics Export:
Because the cameras are physically bolted to extreme metal chassis mounts, their `rvec`, `tvec`, `K`, and `D` parameters **never change** while driving. Therefore, the reverse-mapping projections never change either.

In `stitching_bev.py`, after we calculate exactly which pixel belongs to which patch of dirt, and after we calculate exactly what the overlapping blending weights are, we save those final instructions into highly compressed binary arrays called **Look-Up Tables (LUTs)** (`lut_Cam_Front.npz`).

### The Real-Time Loop:
In `render_bev.py`, the real-time simulation completely bypasses the 3D physics engine. It loads the LUT into RAM (or VRAM on a GPU). Then, 60 times a second, it simply runs a 2D memory swap: "LUT says BEV pixel 500,500 needs color from Camera pixel 753,891 at 45% opacity." It instantly pulls the colors mapping the entire 360-degree image in mere milliseconds using `cv2.remap()`.
