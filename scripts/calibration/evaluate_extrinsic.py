"""
Module: evaluate_extrinsic.py

This module provides functionality related to evaluate extrinsic.
"""

import os
import sys

import cv2
import numpy as np

# Load Intrinsic parameters
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
intrinsic_params_path = os.path.join(
    base_dir, "data/calibration/intrinsic/params/intrinsic_params.npz"
)

if not os.path.exists(intrinsic_params_path):
    print(f"Error: Intrinsic parameters not found at {intrinsic_params_path}")
    sys.exit(1)

with np.load(intrinsic_params_path) as data:
    K = data["K"]
    D = data["D"]

# Ensure debug output folder exists
debug_dir = os.path.join(base_dir, "data/calibration/extrinsic/debug")
os.makedirs(debug_dir, exist_ok=True)


# Define checkerboard geometry identically to calibrate_extrinsic.py
def get_pad_3d_points(center_x, center_y, cam_name):
    square_size = 0.25
    grid_w, grid_h = 7, 5
    objp = np.zeros((grid_w * grid_h, 3), np.float32)

    if cam_name == "Cam_Front":
        start_x = center_x + 2 * square_size
        start_y = center_y + 3 * square_size
        for i in range(grid_h):
            for j in range(grid_w):
                objp[i * grid_w + j] = [
                    start_x - i * square_size,
                    start_y - j * square_size,
                    0,
                ]

    elif cam_name == "Cam_Back":
        start_x = center_x - 2 * square_size
        start_y = center_y - 3 * square_size
        for i in range(grid_h):
            for j in range(grid_w):
                objp[i * grid_w + j] = [
                    start_x + i * square_size,
                    start_y + j * square_size,
                    0,
                ]

    elif cam_name == "Cam_Right":
        start_x = center_x + 3 * square_size
        start_y = center_y - 2 * square_size
        for i in range(grid_h):
            for j in range(grid_w):
                objp[i * grid_w + j] = [
                    start_x - j * square_size,
                    start_y + i * square_size,
                    0,
                ]

    elif cam_name == "Cam_Left":
        start_x = center_x - 3 * square_size
        start_y = center_y + 2 * square_size
        for i in range(grid_h):
            for j in range(grid_w):
                objp[i * grid_w + j] = [
                    start_x + j * square_size,
                    start_y - i * square_size,
                    0,
                ]

    return objp, (grid_w, grid_h)


camera_config = {
    "Cam_Front": (3.5, 0),
    "Cam_Back": (-3.5, 0),
    "Cam_Left": (0, 2),
    "Cam_Right": (0, -2),
}


def verify_camera(cam):
    img_path = os.path.join(base_dir, f"data/calibration/extrinsic/images/{cam}.png")
    extrinsic_path = os.path.join(
        base_dir, f"data/calibration/extrinsic/params/extrinsic_{cam}.npz"
    )

    if not os.path.exists(img_path) or not os.path.exists(extrinsic_path):
        print(f"[{cam}] Missing image or parameters.")
        return

    img = cv2.imread(img_path)

    with np.load(extrinsic_path) as data:
        rvec = data["rvec"]
        tvec = data["tvec"]

    center = camera_config[cam]
    obj_pts, pattern_size = get_pad_3d_points(center[0], center[1], cam)

    # Reproject 3D points back to 2D image plane using Fisheye projectPoints
    # Cv2.fisheye.projectPoints uses 3D points, rvec, tvec, K, D and returns 2D pixel coordinates
    # Note: projectPoints input shape must be (N, 1, 3)
    obj_pts_reshaped = obj_pts.reshape(-1, 1, 3)
    img_pts_proj, _ = cv2.fisheye.projectPoints(obj_pts_reshaped, rvec, tvec, K, D)

    # Calculate Reprojection Error metrics against Actual extracted corners
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, corners = cv2.findChessboardCorners(
        gray, pattern_size, cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE
    )

    if ret:
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)

        # Calculate Error
        error_dist = np.linalg.norm(corners_refined - img_pts_proj, axis=2)
        mean_error = np.mean(error_dist)
        max_error = np.max(error_dist)

        print(
            f"[{cam}] Reprojection Error: Mean = {mean_error:.4f}px, Max = {max_error:.4f}px"
        )
    else:
        print(f"[{cam}] Could not find actual corners to compute mathematical error.")

    # Visualize Reprojected Points
    vis_img = img.copy()
    for pt in img_pts_proj:
        x, y = int(pt[0][0]), int(pt[0][1])
        cv2.circle(
            vis_img, (x, y), 5, (0, 255, 0), -1
        )  # Draw predicted points in Green

    debug_path = os.path.join(debug_dir, f"reproject_{cam}.png")
    cv2.imwrite(debug_path, vis_img)


print("\nVerifying Extrinsics via Reprojection Error...\n" + "-" * 50)
for cam in camera_config.keys():
    verify_camera(cam)
print("-" * 50 + f"\nVisual results saved to: {debug_dir}")
