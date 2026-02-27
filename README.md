# AVM Project - Fisheye Calibration and Simulation rendering

This repository contains a suite of tools for **Automated Fisheye Camera Calibration** and **Surround-View (AVM) Simulation**. It provides a complete pipeline from rendering synthetic calibration data in Blender to calculating high-precision intrinsic parameters and verifying results.

## 🌟 Key Features
- 🤖 **Automated Render Pipeline**: Generate chessboard patterns from multiple perspectives for robust calibration.
- 📐 **Fisheye Lens Model**: Supports OpenCV's equidistant (fisheye) distortion model.
- 💾 **Multi-Format Export**: Saves intrinsic parameters in `.npz` (NumPy) and `.xml` (OpenCV/C++).
- 🏗 **Industrial Structure**: Clean separation between simulation, calibration logic, and data storage.

---

## 📂 Directory Structure

```text
/workspaces/AVM/
├── scripts/
│   ├── simulation/
│   │   ├── generate_calibration_images.py  # Renders chessboard images for calibration
│   │   └── render_surround_view.py         # Renders final surround view images
│   └── calibration/
│       ├── calibrate_intrinsics.py         # Calculates K and D matrices
│       └── verify_calibration.py           # Verifies undistortion using K and D
├── scenes/
│   └── avm_v1.blend                        # Vehicle scene with cameras
│   └── calib_intrinsic.blend               # Dedicated calibration scene
├── data/ (Git ignored)
│   ├── calibration/
│   │   ├── images/                         # Input images for calibration
│   │   ├── debug/                          # Debug visualizations (corners, undistort)
│   │   └── params/                         # Final K and D parameters
│   └── outputs/
│       └── surround_view/                  # Final AVM simulated renders
└── README.md
```

---

## 🚀 Workflow

### 1. Generate Calibration Data (Synthetic)
Renders 15 different perspectives of a checkerboard. Run this inside a Blender instance.
```bash
blender -b scenes/calib_intrinsic.blend -P scripts/simulation/generate_calibration_images.py
```

### 2. Run Intrinsics Calibration
Processes the images and computes the intrinsic matrix `K` and distortion `D`.
```bash
python3 scripts/calibration/calibrate_intrinsics.py
```
*Outputs: `data/calibration/params/intrinsic_params.npz` and `intrinsic_params.xml`.*

### 3. Verify the Calibration
Checks the quality of the calibration by undistorting a test image.
```bash
python3 scripts/calibration/verify_calibration.py
```
*Review the result in `data/calibration/debug/test_undistort.png`.*

### 4. Render Final Surround View
Generates simulated Top-View/AVM perspective renders from the calibrated vehicle cameras.
```bash
blender -b scenes/avm_v1.blend -P scripts/simulation/render_surround_view.py
```

---

## 🛠 Running Environment
- **Docker**: The project is optimized for VS Code DevContainers.
- **Blender**: Requires `blender` executable in PATH (version 3.6+ recommended).
- **Python**: Requires `opencv-python` and `numpy`.

---

## ⚙️ Maintenance
- To add a new camera, update the `cameras` list in `render_surround_view.py`.
- To change the checkerboard size, update `CHECKERBOARD` constant in `calibrate_intrinsics.py`.
