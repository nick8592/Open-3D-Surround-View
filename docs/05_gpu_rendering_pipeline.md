# Real-Time GPU Rendering Pipeline

In traditional automotive surround-view systems, using CPU bound operations (like OpenCV's `cv2.remap`) to de-warp and stitch four high-resolution fisheye camera feeds at 30-60 FPS requires overwhelming processing power.

To achieve production-grade performance, we migrate the heavy lifting (both geometry tracking and pixel interpolation) directly to hardware-accelerated **OpenGL Shaders**.

This document outlines how the mathematical data transfers from Python offline-calibration into real-time GPU memory.

## Architectural Split: Offline Setup vs. Real-Time Rendering
Our pipeline operates in two distinct phases to maximize frame rate:

### 1. Offline Setup (CPU / Python)
You run this phase *once* per vehicle layout, usually at the factory or the end of a calibration routine.
*   **Generate Topology:** `build_bowl.py` calculates the polar mathematics and outputs a curved 3D topology (`svm_pure_bowl.obj`).
*   **Generate Parameters:** The camera intrinsic vectors and physical mounting positions are evaluated.
*   **Calculate Extrinsic Stitching:** `stitching_bowl.py` determines exactly which pixel on the 3D bowl maps to which original camera pixel, factoring in overlaps, creating massive arrays of integers (`map_x`, `map_y`).

### 2. The Bridge (Asset Export)
OpenGL Fragment Shaders do not natively compute OpenCV's mapping format. We use `export_gpu_assets.py` to translate the offline parameters into **raw binary buffers** (`.bin` files) that a graphics card can instantly swallow into VRAM via `glTexImage2D()`.
*   **UV Normalization:** Translates `0 - 1920` width integers into `0.0 - 1.0` normalized floating-point maps.
*   **Mask Compression:** Compacts the intricate feathering/blending boundaries of our 4 overlapping cameras into a single, high-efficiency 4-channel `RGBA32F` floating-point texture (`blend_mask.bin`).

### 3. Real-Time Execution (GPU / PyOpenGL)
This step executes constantly in a loop (`render_bowl_opengl.py`), acting as our vehicle's infotainment ECU.
1.  **Vertex Shader (`svm_bowl.vert`)**: Computes the Model-View-Projection (MVP) matrices to scale our `svm_pure_bowl.obj` vertices, handing off texture coordinates to the following stage. 
2.  **Fragment Shader (`svm_bowl.frag`)**: This is the heart of the engine! For every single pixel on the dashboard screen:
    *   It samples the mapped 3D UV coordinate against our loaded mathematical LUT floats.
    *   It grabs the precise overlapping colors from the 4 raw camera textures.
    *   It samples the Alpha `blend_mask` to multiply the colors conditionally, eliminating seams.
    *   Outputs the beautifully smooth composite pixel frame instantly.

## How to Test the GPU Pipeline
*(Ensure you have run the CPU `stitching_bowl.py` first so the root `luts/` exist)*

1. Compile the arrays to GPU Floating-Point formats:
   ```bash
   python3 scripts/gpu_render/export_gpu_assets.py
   ```
2. Trigger the High-Performance Hardware pipeline natively:
   *(Running headless with Xvfb inside Docker to output `gpu_preview.png`)*
   ```bash
   xvfb-run -s "-screen 0 1280x720x24" python3 scripts/gpu_render/render_bowl_opengl.py
   ```