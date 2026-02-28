# AVM Calibration Theory & Coordinate Systems

## 1. The Automotive Coordinate System (ISO 8855)
When dealing with multi-camera systems on a physical vehicle, the most important foundational step is establishing a universal "World Origin". This project strictly adheres to the **ISO 8855** standard:

*   **Origin (0, 0, 0):** The physical center of the rear axle on the ground.
*   **+X Axis:** Points strictly FORWARD (through the windshield).
*   **+Y Axis:** Points strictly LEFT (through the driver-side door, assuming LHD).
*   **+Z Axis:** Points strictly UP (through the roof).

By adhering to this standard, all camera positions (translations) and rotations (Euler Angles: Yaw, Pitch, Roll) are universally understandable. For instance, a camera with translation `X=3.5, Y=0, Z=1.0` is exactly 3.5 meters in front of the rear axle, perfectly centered, and 1 meter off the ground (e.g., standard front bumper camera).

## 2. Intrinsic Calibration (The Lens Physics)
Fisheye lenses capture nearly 180-degree fields of view but introduce severe "barrel distortion," where straight lines bend significantly at the edges.

Intrinsic calibration extracts two mathematical matrices that describe this distortion:
1.  **The Camera Matrix (`K`):** Contains the Focal Length (`fx, fy`) and Optical Center (`cx, cy`). This defines how light passes through the lens and hits the sensor.
2.  **The Distortion Coefficients (`D`):** In this project, we use OpenCV's **Equidistant Fisheye Model**. It generates 4 coefficients (`k1, k2, k3, k4`) representing a polynomial curve that dictates exactly how pixels compress and bend as they move away from the optical center.

By finding a checkerboard pattern from multiple angles in `calibrate_intrinsic.py`, the algorithm reverse-engineers the bending of the light to compute `K` and `D`.

## 3. Extrinsic Calibration (The Physical Mount)
Extrinsic parameters describe exactly *where* the camera is mounted on the car and exactly *where* it is looking.

*   **Translation Vector (`tvec`):** The X, Y, Z physical distance from the ISO 8855 World Origin to the Camera's sensor.
*   **Rotation Vector (`rvec`):** The 3D orientation of the camera (which way it is facing). OpenCV outputs this as an axis-angle representation (Rodrigues vector).

### How Extrinsics are calculated:
In `calibrate_extrinsic.py`, we place checkerboard mats on the ground at known, exact physical coordinates around the car (e.g., exactly 2 meters left of center). Because the camera spots the checkerboard, and we feed the script the *real* physical coordinates of that checkerboard, the `cv2.solvePnP` function calculates the exact reverse mathematical path to figure out the camera's height and rotation.
