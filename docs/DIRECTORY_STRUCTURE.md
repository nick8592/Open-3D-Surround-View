# Repository Directory Structure

This document provides a detailed overview of the mathematical, rendering, and logic pipelines spread across the directory tree. It illustrates how the synthetic scenes break down into calibration metrics, rendering tables, and final output.

```text
/workspaces/Open-3D-Surround-View/
├── data/ (Locally generated assets & outputs)
│   ├── bev_2d/                             
│   │   ├── debug/                          # Photometric error heatmaps for camera overlap regions
│   │   ├── luts/                           # Production Look-Up Tables (LUTs) for rapid flat-plane BEV mapping
│   │   ├── bev.png                         # High-res stitched 2D ground plane
│   │   └── realtime_demo_bev.png           # Simulated 2D dashboard UX output (Flat Plane)
│   ├── bowl_3d/
│   │   ├── luts/                           # Physical Extrinsic LUTs for curved 3D topology projection
│   │   ├── svm_pure_bowl.obj               # Mathematically pure 3D Bowl Mesh (.obj)
│   │   ├── svm_pure_bowl.mtl               # MTL shader coordinates mapping to UV values
│   │   ├── bowl_texture.png                # Distorted 2D mapped texture array (wrapped over 3D model)
│   │   └── realtime_demo_bowl.png          # Simulated Real-time ECU dashboard 3D UI
│   ├── calibration/
│   │   ├── extrinsic/
│   │   │   ├── debug/                      # Visual mathematical reprojection error overlays
│   │   │   ├── images/                     # Source images from the 4 fisheye cameras on car
│   │   │   └── params/                     # Final Extrinsic ZYX rotation & translation matrices (.npz/.xml)
│   │   └── intrinsic/
│   │       ├── debug/                      # Extracted 2D vs 3D corners and plumb-lines for distortion checking
│   │       ├── images/                     # Input simulated checkerboard patterns for K/D extraction
│   │       └── params/                     # Final Intrinsic Lens K and D matrices (.npz/.xml)
│   └── sample/                             
│       └── ...                             # Built-in front/left/right/back fisheye captures for Quick Start demo
├── demo/                                   
│   ├── demo.py                             # Master Quick-Start script combining parameters & rendering passes
│   └── export_yaml.py                      # Generates standard readable YAML from the calibration parameters
├── docs/                                   
│   ├── images/                             # Contains preview/demo output imagery injected into the README
│   └── DIRECTORY_STRUCTURE.md              # This file
├── scenes/                                 # 3D Topology Assets
│   ├── svm_v1.blend                        # Core vehicle mounting & camera rig Blender scene
│   └── calib_intrinsic.blend               # Synthetic room used exclusively to capture 15 checking angles
├── scripts/                                # Mathematics and Physics Source Code
│   ├── bev_2d/
│   │   ├── evaluate_bev.py                 # Evaluates flat stitching alignment via Sub-pixel Photometric error checking
│   │   ├── render_bev.py                   # High-performance simulation loop evaluating flat plane real-time rendering
│   │   └── stitching_bev.py                # Maps logical Flat Ground boundaries and generates memory-cached LUTs
│   ├── blender_render/
│   │   ├── preview_3d_bowl.py              # Opens a UI environment visually importing Z-Up geometry to audit the final topological output 
│   │   └── render_cinematic.py             # Executes a simulated flying chase camera spin around the 3D Bowl to export cinematic video
│   ├── bowl_3d/
│   │   ├── build_bowl.py                   # Solves strict polar mathematics to construct clean 3D Bowl geometry rulesets
│   │   ├── render_bowl.py                  # High-performance GUI 3D Projection loop simulating a dashboard dashboard execution
│   │   └── stitching_bowl.py               # Generates mapping UVs bridging the 4 Extrinsic fisheye feeds logically over a curved Z-Up wall
│   ├── calibration/
│   │   ├── calibrate_extrinsic.py          # Core logic solving Physical Orientation (Yaw/Pitch/Roll) arrays
│   │   ├── calibrate_intrinsic.py          # System detecting checkerboard intersections to forge K Matrix bounds
│   │   ├── evaluate_extrinsic.py           # Projects perfect mathematical coordinates backward onto images to generate Reprojection MAE parameters
│   │   └── evaluate_intrinsic.py           # Validates lens un-distortion formulas analyzing curve-corrected straight-line metrics
│   ├── synthetic_capture/
│   │   ├── capture_extrinsic.py            # Automated control script manipulating Blender to fire static cameras in SVM frame
│   │   └── capture_intrinsic.py            # Automated sweep rendering multi-angle testing environments for lens detection
│   └── utils/
│       └── generate_visuals.py             # Internal helper script to automatically generate dynamic README comparison images and animations
├── .devcontainer/                          # Automated setup container mounting OpenCV / Blender bindings directly for Visual Studio Code IDEs
├── config.py                               # Centralized tuning parameters describing the vehicle dimension and rendering margins
├── Dockerfile                              # Core system configuration ensuring consistent environment execution paths
├── README.md                               # Root instructional file describing the Quick Start mechanics
└── requirements.txt                        # Locked dependency mapping restricting package incompatibility (e.g. OpenCV / Numpy C-API bindings)
```
