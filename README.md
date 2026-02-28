# Open-3D-Surround-View

This repository contains a comprehensive suite of tools for **Automated Fisheye Camera Calibration** and **Surround-View Monitor (AVM) Simulation**. It provides a complete end-to-end pipeline: starting from rendering synthetic calibration checkerboards in Blender, to calculating high-precision intrinsic (K and D) and extrinsic (rvec, tvec, Euler Angles) camera parameters using OpenCV, and rigorously verifying the results through mathematical reprojection error metrics.

## 🌟 Key Features
- 🤖 **Automated Render Pipeline**: Programmatically generate simulated chessboard images inside Blender from multiple perspectives to ensure robust calibration data.
- 📐 **Fisheye Lens Model**: Fully supports OpenCV's robust equidistant (fisheye) distortion model for ultra-wide lenses.
- 🧭 **ISO 8855 Automotive Standard**: All 3D math and extracted Euler angles natively adhere to the standard vehicle coordinate system (X=Forward, Y=Left, Z=Up).
- 📊 **Precision Verification**: Built-in verification scripts analyze sub-pixel mean reprojection error and generate visual corner overlays to guarantee mathematical accuracy.
- 💾 **Multi-Format Export**: Saves all camera parameters in accessible `.npz` (NumPy) formats and `.xml` for seamless integration into OpenCV/C++ environments.
- 🏗 **Industrial Structure**: Clean, modular separation between Blender simulation scripts, Python camera calibration logic, and organized data storage paths.

---

## 🧭 Coordinate System (ISO 8855)

The entire calibration pipeline, 3D math, and exported variables adhere strictly to the **ISO 8855 Automotive Standard (Right-Handed, Z-Up)**:
- **+X Axis**: Points **Forward** (Through the vehicle's front windshield)
- **+Y Axis**: Points **Left** (Through the driver's side door)
- **+Z Axis**: Points **Up** (Through the roof)

Euler angles (Yaw, Pitch, Roll) extracted from `calibrate_extrinsic.py` are natively aligned to `ZYX` intrinsic automotive rotations.

## 📂 Directory Structure

```text
/workspaces/AVM/
├── docs/                                   # Theory, logic, and mathematics documentation
│   ├── 01_camera_calibration.md
│   ├── 02_bev_2d_mapping.md
│   ├── 03_bowl_3d_mapping.md
│   └── 04_evaluation_metrics.md
├── scripts/
│   ├── simulation/
│   │   ├── capture_intrinsic.py            # Renders chessboard images for intrinsic calibration
│   │   ├── capture_extrinsic.py            # Captures images for extrinsic calibration
│   │   └── preview_3d_bowl.py              # Opens Blender specifically to view Z-up generated meshes
│   ├── bowl_3d/
│   │   ├── build_bowl.py                   # Constructs clean, mathematical 3D Bowl topology (`avm_pure_bowl.obj`)
│   │   ├── stitching_bowl.py               # Calculates exact physical Extrinsic physics for curved 3D walls
│   │   └── render_bowl.py                  # Simulated Real-time ECU dashboard rendering engine (13+ FPS)
│   ├── calibration/
│       ├── calibrate_intrinsic.py          # Calculates intrinsic K and D matrices
│       ├── evaluate_intrinsic.py           # Evaluates undistortion using K and D and curvature variance
│       ├── calibrate_extrinsic.py          # Calculates extrinsic rvec and tvec matrices
│       └── evaluate_extrinsic.py           # Evaluates extrinsics via 3D reprojection error
│   └── bev_2d/
│       ├── stitching_bev.py                # Maps logical BEV and exports optimized map/weight LUTs
│       ├── render_bev.py                   # Real-time simulation loop that loads LUTs to stitch LIVE frames
│       └── evaluate_bev.py                 # Evaluates stitching alignment via photometric error
├── scenes/
│   └── avm_v1.blend                        # Vehicle scene with cameras
│   └── calib_intrinsic.blend               # Dedicated calibration scene
├── data/ (Git ignored)
│   ├── calibration/
│   │   ├── intrinsic/
│   │   │   ├── images/                         # Input images for intrinsic calibration
│   │   │   ├── debug/                          # Debug visualizations (corners, undistort)
│   │   │   └── params/                         # Final K and D parameters
│   │   └── extrinsic/
│   │       ├── images/                         # Input images for extrinsic calibration
│   │       ├── debug/                          # Debug visualizations (corners, overlays)
│   │       └── params/                         # Final rvec and tvec parameters
│   └── outputs/
│       └── surround_view/                  # Final AVM simulated renders
│   └── stitching/
│       ├── debug/                          # Intermediate BEV projections and evaluation heatmaps
│       └── bev.png                         # Final stitched Bird's Eye View output
└── README.md
```

---

## 📖 Technical Documentation

For developers seeking to understand the background physics, mathematical models, and architectural decisions powering this pipeline, please refer to the dedicated theory guides:

1. [Calibration Theory & Coordinate Systems](docs/01_camera_calibration.md): Explains ISO 8855 standard geometry, fisheye intrinsic mathematical formulation, and extrinsic point-matching physics.
2. [2D BEV Mapping & Look-Up Tables (LUT)](docs/02_bev_2d_mapping.md): Details the reverse-projection math from the flat Z=0 ground plane and the hardware-accelerated Extrinsic LUT optimizations used for real-time dashboard ECU operation.
3. [3D Bowl Projection Architecture](docs/03_bowl_3d_mapping.md): Mathematically details the industry transition from flat representations to curved 3D topology (Z > 0 walls) to solve Spider-Leg corner stretching and Parallax flat-mat ghosting.
4. [Evaluation Metrics & Precision](docs/04_evaluation_metrics.md): Breaks down the "Holy Trinity" of calibration proofs including Plumb-Line Curvature, Extrinsic Sub-Pixel Reprojection, and overlapping Photometric Area tracking.

---

## 🚀 Workflow

The AVM pipeline is structurally split into 3 logical phases: **Lens Calibration (Intrinsic)**, **Robot Assembly (Extrinsic)**, and **Surround View Simulation (Stitching)**.

---

### Phase 1: Intrinsic Lens Calibration
*Determining the internal physical profile of the fisheye lenses (`K` and `D` matrices).*

**Step 1.1: Capture Intrinsic Images (Synthetic)**
Renders 15 different perspectives of a checkerboard. Run this inside a Blender instance.
```bash
blender -b scenes/calib_intrinsic.blend -P scripts/simulation/capture_intrinsic.py
```

**Step 1.2: Run Intrinsics Calibration**
Processes the images and computes the intrinsic matrix `K` and distortion `D`.
```bash
python3 scripts/calibration/calibrate_intrinsic.py
```
*Outputs: `data/calibration/intrinsic/params/intrinsic_params.npz` and `intrinsic_params.xml`.*

**Step 1.3: Evaluate the Intrinsic Calibration**
Checks the quality of the calibration by undistorting a test image and calculating plumb-line curvature variance.
```bash
python3 scripts/calibration/evaluate_intrinsic.py
```
*Review the result in `data/calibration/intrinsic/debug/test_plumbline.png`.*

---

### Phase 2: Extrinsic System Calibration
*Determining the physical mounting position and orientation of the cameras on the vehicle (`rvec` and `tvec`)*.

**Step 2.1: Capture Extrinsic Images**
Renders the 4 vehicle cameras positioned around the ISO 8855 extrinsics checkerboard setup.
```bash
blender -b scenes/avm_v1.blend -P scripts/simulation/capture_extrinsic.py
```

**Step 2.2: Run Extrinsic Calibration**
Calculates the physical translation and rotation for each camera.
```bash
python3 scripts/calibration/calibrate_extrinsic.py
```
*Outputs: Per-camera `.npz` and `.xml` files in `data/calibration/extrinsic/params/`.*

**Step 2.3: Evaluate Extrinsic Calibration**
Mathematically projects the 3D world points back onto the images to calculate sub-pixel reprojection error metrics.
```bash
python3 scripts/calibration/evaluate_extrinsic.py
```
*Outputs: Error metrics in terminal and visual overlays in `data/calibration/extrinsic/debug/reproject_*.png`.*

---

### Phase 3: BEV Mapping & Real-Time Simulation
*Mapping the calibrated cameras onto a unified Ground Plane (Z=0) and optimizing for 60FPS dashboard deployment.*

**Step 3.1: Generate BEV Mapping (Look-Up Tables)**
Maps all 4 fisheye cameras onto a unified 3D physical ground plane to calculate rendering coordinates & alpha weights.
Executes the heavy math exactly once, and stores the rulesets (`.npz` LUTs) to memory.
```bash
python3 scripts/bev_2d/stitching_bev.py
```
*Outputs: Optimized `lut_{Cam}.npz` pre-calculated matrices inside `data/bev_2d/luts/`.*

**Step 3.2: Simulate Real-Time BEV Rendering**
Wraps the actual real-world loop. Loads the pre-computed Look-Up Tables into RAM, ingests live camera frames, and instantly maps/stitches the `Bird's-Eye View` composite simulating high FPS performance tracking.
```bash
python3 scripts/bev_2d/render_bev.py
```
*Outputs: Evaluated python runtime metrics (e.g. `~14 FPS`) and the final `realtime_demo_bev.png`.*

**Step 3.3: Evaluate Stitching Alignment**
Mathematically crops and compares shared overlapping sightlines to quantify Extrinsic photometric error.
```bash
python3 scripts/bev_2d/evaluate_bev.py
```
*Outputs: MAE and RMSE error metrics per corner, and a colorized visual heatmap in `data/bev_2d/debug/`.*

**Step 3.4: Generate Perfect 3D Bowl Geometry**
Mathematically constructs a flawless Z-up Polar 3D Bowl topology based on ISO 8855 Coordinate constraints without Spider Leg stretching or Parallax ghosting.
```bash
python3 scripts/bowl_3d/build_bowl.py
```
*Outputs: Clean pure mesh `avm_pure_bowl.obj` (with UV mappings) and `avm_pure_bowl.mtl`.*

**Step 3.5: Calculate Extrinsic UV Mappings for the 3D Bowl**
Reruns the rigorous 3D world physics engine. Unlike the flat 2D projection, it accounts for the actual curvature Z-Height to project physical wall textures flawlessly outwards into the fisheye cameras without severe stretching.
```bash
python3 scripts/bowl_3d/stitching_bowl.py
```
*Outputs: Advanced alpha-blended UV arrays (`lut_bowl_{Cam}.npz`) and a `bowl_texture.png` preview.*

**Step 3.6: Simulate Real-Time 3D ECU Rendering**
Ingests the newly calculated 3D Extrinsic LUTs and spins up a high-performance vector rendering loop simulating the dashboard display.
```bash
python3 scripts/bowl_3d/render_bowl.py
```
*Outputs: Simulated runtime metrics (~15 FPS natively in Python) and `realtime_demo_bowl.png`.*

**Step 3.7: Preview the generated 3D Bowl Array in 3D Space**
Opens a Blender instance and imports the geometry strictly preserving Z-Up formatting, auto-connecting the material shaders to visually verify the mathematical projection perfection on the 3D model.
```bash
blender -P scripts/simulation/preview_3d_bowl.py
```

---

## 🛠 Running Environment
- **Docker**: The project is optimized for VS Code DevContainers.
- **Blender**: Requires `blender` executable in PATH (version 3.6+ recommended).
- **Python**: Requires `opencv-python` and `numpy`.

---

## ⚙️ Maintenance
- To add a new camera, update the `cameras` list in `capture_extrinsic.py`.
- To change the checkerboard size, update `CHECKERBOARD` constant in `calibrate_intrinsic.py` and `calibrate_extrinsic.py`.
