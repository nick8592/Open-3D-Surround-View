# AVM Project - Fisheye Calibration and Simulation rendering

This repository contains a suite of tools for **Automated Fisheye Camera Calibration** and **Surround-View (AVM) Simulation**. It provides a complete pipeline from rendering synthetic calibration data in Blender to calculating high-precision intrinsic parameters and verifying results.

## 🌟 Key Features
- 🤖 **Automated Render Pipeline**: Generate chessboard patterns from multiple perspectives for robust calibration.
- 📐 **Fisheye Lens Model**: Supports OpenCV's equidistant (fisheye) distortion model.
- 💾 **Multi-Format Export**: Saves intrinsic parameters in `.npz` (NumPy) and `.xml` (OpenCV/C++).
- 🏗 **Industrial Structure**: Clean separation between simulation, calibration logic, and data storage.

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
├── scripts/
│   ├── simulation/
│   │   ├── capture_intrinsic.py            # Renders chessboard images for intrinsic calibration
│   │   └── capture_extrinsic.py            # Captures images for extrinsic calibration
│   └── calibration/
│       ├── calibrate_intrinsic.py          # Calculates intrinsic K and D matrices
│       ├── verify_intrinsic.py             # Verifies undistortion using K and D
│       └── calibrate_extrinsic.py          # Calculates extrinsic rvec and tvec matrices
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
└── README.md
```

---

## 🚀 Workflow

### 1. Capture Intrinsic Images (Synthetic)
Renders 15 different perspectives of a checkerboard. Run this inside a Blender instance.
```bash
blender -b scenes/calib_intrinsic.blend -P scripts/simulation/capture_intrinsic.py
```

### 2. Run Intrinsics Calibration
Processes the images and computes the intrinsic matrix `K` and distortion `D`.
```bash
python3 scripts/calibration/calibrate_intrinsic.py
```
*Outputs: `data/calibration/intrinsic/params/intrinsic_params.npz` and `intrinsic_params.xml`.*

### 3. Verify the Intrinsic Calibration
Checks the quality of the calibration by undistorting a test image.
```bash
python3 scripts/calibration/verify_intrinsic.py
```
*Review the result in `data/calibration/intrinsic/debug/test_undistort.png`.*

### 4. Capture Extrinsic Images
Renders the 4 vehicle cameras positioned around the extrinsics checkerboard setup.
```bash
blender -b scenes/avm_v1.blend -P scripts/simulation/capture_extrinsic.py
```

### 5. Run Extrinsic Calibration
Calculates the physical translation and rotation (rvec/tvec) for each camera.
```bash
python3 scripts/calibration/calibrate_extrinsic.py
```
*Outputs: Per-camera `.npz` and `.xml` files in `data/calibration/extrinsic/params/`.*

---

## 🛠 Running Environment
- **Docker**: The project is optimized for VS Code DevContainers.
- **Blender**: Requires `blender` executable in PATH (version 3.6+ recommended).
- **Python**: Requires `opencv-python` and `numpy`.

---

## ⚙️ Maintenance
- To add a new camera, update the `cameras` list in `capture_extrinsic.py`.
- To change the checkerboard size, update `CHECKERBOARD` constant in `calibrate_intrinsic.py` and `calibrate_extrinsic.py`.
