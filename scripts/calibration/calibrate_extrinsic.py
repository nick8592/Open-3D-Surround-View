"""
Module: calibrate_extrinsic.py

This module provides functionality related to calibrate extrinsic.
"""

import os
import sys

import cv2
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
import config

# 1. Load Intrinsic parameters dynamically
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
params_path = os.path.join(
    base_dir, "data/calibration/intrinsic/params/intrinsic_params.npz"
)

if not os.path.exists(params_path):
    print(f"Error: Intrinsic parameters not found at {params_path}")
    sys.exit(1)

with np.load(params_path) as data:
    K = data["K"]
    D = data["D"]
print(f"Loaded intrinsic parameters from {params_path}")


def get_pad_3d_points(center_x, center_y, cam_name):
    square_size = config.EXTRINSIC_CALIB_SQUARE_SIZE
    grid_w, grid_h = (
        config.EXTRINSIC_CALIB_PATTERN_W,
        config.EXTRINSIC_CALIB_PATTERN_H,
    )  # corners along width (image X) and height (image Y)
    objp = np.zeros((grid_w * grid_h, 3), np.float32)

    if cam_name == "Cam_Front":
        # Image Top -> +X (further Forward)
        # Image Left -> +Y (Left)
        start_x = center_x + 2 * square_size
        start_y = center_y + 3 * square_size
        for i in range(grid_h):  # Image down -> X decreases
            for j in range(grid_w):  # Image right -> Y decreases
                objp[i * grid_w + j] = [
                    start_x - i * square_size,
                    start_y - j * square_size,
                    0,
                ]

    elif cam_name == "Cam_Back":
        # Image Top -> -X (further Backward)
        # Image Left -> -Y (Right)
        start_x = center_x - 2 * square_size
        start_y = center_y - 3 * square_size
        for i in range(grid_h):  # Image down -> X increases
            for j in range(grid_w):  # Image right -> Y increases
                objp[i * grid_w + j] = [
                    start_x + i * square_size,
                    start_y + j * square_size,
                    0,
                ]

    elif cam_name == "Cam_Right":
        # Image Top -> -Y (further Right)
        # Image Left -> +X (Forward)
        start_x = center_x + 3 * square_size
        start_y = center_y - 2 * square_size
        for i in range(grid_h):  # Image down -> Y increases
            for j in range(grid_w):  # Image right -> X decreases
                objp[i * grid_w + j] = [
                    start_x - j * square_size,
                    start_y + i * square_size,
                    0,
                ]

    elif cam_name == "Cam_Left":
        # Image Top -> +Y (further Left)
        # Image Left -> -X (Backward)
        start_x = center_x - 3 * square_size
        start_y = center_y + 2 * square_size
        for i in range(grid_h):  # Image down -> Y decreases
            for j in range(grid_w):  # Image right -> X increases
                objp[i * grid_w + j] = [
                    start_x + j * square_size,
                    start_y - i * square_size,
                    0,
                ]

    return objp, (grid_w, grid_h)


def solve_extrinsic_for_camera(cam_name, pad_center):
    img_path = f"data/calibration/extrinsic/images/{cam_name}.png"
    img = cv2.imread(img_path)
    if img is None:
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    obj_pts, pattern_size = get_pad_3d_points(pad_center[0], pad_center[1], cam_name)

    # --- 1. CORNER DETECTION ---
    # ATTEMPT 1: Try OpenCV 4's robust Sector-Based corner detection algorithm.
    # SB handles noise and fisheye distortion much better, but can fail if calibration squares are too small.
    ret, corners_refined = cv2.findChessboardCornersSB(
        gray, pattern_size, cv2.CALIB_CB_EXHAUSTIVE | cv2.CALIB_CB_ACCURACY
    )
    
    # ATTEMPT 2: Fallback to classical OpenCV corner detection with CLAHE
    if not ret:
        # If squares are small or lighting is difficult, SB might fail. We use CLAHE 
        # (Contrast Limited Adaptive Histogram Equalization) to strongly enhance local contrast, 
        # then pass it to the classical detector, which is often more forgiving for small features.
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        cl1 = clahe.apply(gray)
        ret, corners = cv2.findChessboardCorners(
            cl1, pattern_size, cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE
        )
        if ret:
            # Unlike SB, the classical algorithm requires a manual sub-pixel refinement step.
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)

    if ret:
        # --- 2. SOLVE PNP WITH AUTOMATIC ORIENTATION CORRECTION ---
        # OpenCV expects pinhole projection, but we have fisheye lenses. We MUST 
        # undistort the 2D corner points first before passing them to solvePnP.
        
        # CRITICAL DESIGN LOGIC: solvePnP maps the list of 2D corners to our 3D object points.
        # Depending on the camera's angle and which OpenCV detector algorithm succeeded, 
        # the array of found corners might be in the exact reverse order of our 3D points array!
        # If passed directly to solvePnP, it will falsely place the camera on the FAR SIDE of the pad.
        # To make this robust, we evaluate both orientations and pick the mathematically correct one.
        undistorted1 = cv2.fisheye.undistortPoints(
            corners_refined.reshape(-1, 1, 2), K, D, P=K
        )
        undistorted2 = cv2.fisheye.undistortPoints(
            corners_refined[::-1].reshape(-1, 1, 2), K, D, P=K
        )

        def eval_pose(undistorted_corners):
            success, rvec, tvec = cv2.solvePnP(
                obj_pts, undistorted_corners, K, None, flags=cv2.SOLVEPNP_SQPNP
            )
            if not success:
                return None, float('inf')
            
            R, _ = cv2.Rodrigues(rvec)
            camera_pos = -np.matrix(R).T * np.matrix(tvec)
            # Distance from camera to car center in X/Y plane
            dist_to_center = np.hypot(camera_pos[0,0], camera_pos[1,0])
            return (rvec, tvec, camera_pos), dist_to_center

        pose1, dist1 = eval_pose(undistorted1)
        pose2, dist2 = eval_pose(undistorted2)

        if pose1 is None and pose2 is None:
            return None

        # The camera on the car MUST be closer to the car center than the calibration pad on the floor outside.
        # solvePnP with reversed corners places the camera on the FAR side of the pad.
        best_pose = pose1 if dist1 < dist2 else pose2
        rvec, tvec, camera_pos = best_pose

        # Debug Visualization
        vis_img = img.copy()
        cv2.drawChessboardCorners(vis_img, pattern_size, corners_refined if dist1 < dist2 else corners_refined[::-1], ret)
        
        # Red circle at the FIRST corner to verify ordering
        first_corner = corners_refined[0][0] if dist1 < dist2 else corners_refined[::-1][0][0]
        cv2.circle(vis_img, tuple(first_corner.astype(int)), 15, (0, 0, 255), -1)

        debug_dir = "data/calibration/extrinsic/debug"
        os.makedirs(debug_dir, exist_ok=True)
        cv2.imwrite(os.path.join(debug_dir, f"debug_{cam_name}.png"), vis_img)

        # Extract Pitch, Yaw, Roll using Scipy Extrinsic ZXY mapping
        R, _ = cv2.Rodrigues(rvec)
        R_cw = np.matrix(R).T
        R_base = np.array([[0, 0, 1], [-1, 0, 0], [0, -1, 0]])
        from scipy.spatial.transform import Rotation as R_scipy

        R_veh = R_cw @ np.linalg.inv(R_base)
        yaw, pitch, roll = R_scipy.from_matrix(R_veh).as_euler("ZYX", degrees=True)

        print(f"  {cam_name} Success!")
        print(f"    World Position: X={camera_pos[0,0]:.3f}m, Y={camera_pos[1,0]:.3f}m, Z={camera_pos[2,0]:.3f}m")
        print(f"    Rotation: Yaw={yaw:.1f}°, Pitch={pitch:.1f}°, Roll={roll:.1f}°")

        return (rvec, tvec)
    return None


results = {}
output_dir = "data/calibration/extrinsic/params"
os.makedirs(output_dir, exist_ok=True)
for cam, pad_center in config.CALIB_PAD_CENTER.items():
    print(f"Solving {cam}...")
    ext = solve_extrinsic_for_camera(cam, pad_center)
    if ext:
        rvec, tvec = ext[0], ext[1]
        results[cam] = {"rvec": rvec, "tvec": tvec}

        # Save individual .npz
        npz_path = os.path.join(output_dir, f"extrinsic_{cam}.npz")
        np.savez(npz_path, rvec=rvec, tvec=tvec)

        # Save individual .xml
        xml_path = os.path.join(output_dir, f"extrinsic_{cam}.xml")
        fs = cv2.FileStorage(xml_path, cv2.FILE_STORAGE_WRITE)
        fs.write("rvec", rvec)
        fs.write("tvec", tvec)
        fs.release()

    else:
        print(f"  {cam} Failed.")

np.savez(os.path.join(output_dir, "extrinsics_all.npz"), **results)
print(f"\nAll extrinsics saved successfully in {output_dir}")
