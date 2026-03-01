"""
Module: evaluate_bev.py

This module provides functionality related to evaluate bev.
"""

import os
import sys

import cv2
import numpy as np

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

if base_dir not in sys.path:
    sys.path.append(base_dir)

import config

PIXELS_PER_METER = config.PIXELS_PER_METER
BEV_WIDTH = config.BEV_WIDTH
BEV_HEIGHT = config.BEV_HEIGHT
X_RANGE = config.X_RANGE
Y_RANGE = config.Y_RANGE
CAR_LENGTH = config.CAR_LENGTH
CAR_WIDTH = config.CAR_WIDTH
intrinsic_params_path = os.path.join(
    base_dir, "data/calibration/intrinsic/params/intrinsic_params.npz"
)
extrinsic_dir = os.path.join(base_dir, "data/calibration/extrinsic/params")
images_dir = os.path.join(base_dir, "data/calibration/extrinsic/images")
debug_dir = os.path.join(base_dir, "data/bev_2d/debug")
os.makedirs(debug_dir, exist_ok=True)

# Load intrinsics
if not os.path.exists(intrinsic_params_path):
    print(f"Error: Intrinsic parameters not found at {intrinsic_params_path}")
    sys.exit(1)

with np.load(intrinsic_params_path) as data:
    K = data["K"]
    D = data["D"]

cameras = ["Cam_Front", "Cam_Left", "Cam_Back", "Cam_Right"]
print("Initializing 3D spatial mapping grid for Evaluation...")
u, v = np.meshgrid(np.arange(BEV_WIDTH), np.arange(BEV_HEIGHT))
X = X_RANGE[1] - (v / PIXELS_PER_METER)
Y = Y_RANGE[1] - (u / PIXELS_PER_METER)
Z = np.zeros_like(X)
pts_3d = np.stack((X, Y, Z), axis=-1).reshape(-1, 1, 3).astype(np.float32)

camera_data = {}

for cam in cameras:
    ext_path = os.path.join(extrinsic_dir, f"extrinsic_{cam}.npz")
    img_path = os.path.join(images_dir, f"{cam}.png")

    with np.load(ext_path) as edata:
        rvec = edata["rvec"]
        tvec = edata["tvec"]

    img = cv2.imread(img_path)
    img_h, img_w = img.shape[:2]

    R, _ = cv2.Rodrigues(rvec)
    pts_cam = R @ pts_3d.reshape(-1, 3).T + tvec
    z_cam = pts_cam[2, :].reshape(BEV_HEIGHT, BEV_WIDTH)

    pts_2d, _ = cv2.fisheye.projectPoints(pts_3d, rvec, tvec, K, D)
    pts_2d = pts_2d.reshape(BEV_HEIGHT, BEV_WIDTH, 2)
    map_x = pts_2d[..., 0].astype(np.float32)
    map_y = pts_2d[..., 1].astype(np.float32)

    warped = cv2.remap(
        img,
        map_x,
        map_y,
        cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0),
    )
    # Convert to grayscale to remove color dependence from alignment metrics
    warped_gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)

    # Absolute strict valid mask (must be physical, in-sensor, and not on the car itself)
    valid_mask = (
        (z_cam > 0)
        & (map_x >= 0)
        & (map_x < img_w - 1)
        & (map_y >= 0)
        & (map_y < img_h - 1)
    )
    car_mask = (X > -CAR_LENGTH / 2.0) & (X < CAR_LENGTH / 2.0) & (Y > -CAR_WIDTH / 2.0) & (Y < CAR_WIDTH / 2.0)
    valid_mask = valid_mask & (~car_mask)

    camera_data[cam] = {
        "warped_gray": warped_gray,
        "warped_color": warped,
        "mask": valid_mask,
    }

# Overlap evaluation pairs
pairs = [
    ("Cam_Front", "Cam_Left"),
    ("Cam_Front", "Cam_Right"),
    ("Cam_Back", "Cam_Left"),
    ("Cam_Back", "Cam_Right"),
]

print("\n" + "=" * 50)
print("Evaluating Overlap Alignment (Photometric Error)")
print("=" * 50)

# Create a master heat map to show where errors are happening
heat_map = np.zeros((BEV_HEIGHT, BEV_WIDTH), dtype=np.float32)

all_maes = []

for cam_a, cam_b in pairs:
    data_a = camera_data[cam_a]
    data_b = camera_data[cam_b]

    # Find identical physical pixels seen by BOTH cameras
    overlap_mask = data_a["mask"] & data_b["mask"]
    num_overlapping_pixels = np.sum(overlap_mask)

    if num_overlapping_pixels == 0:
        print(f"[{cam_a} & {cam_b}]: No overlap detected!")
        continue

    img_a_vals = data_a["warped_gray"][overlap_mask].astype(np.float32)
    img_b_vals = data_b["warped_gray"][overlap_mask].astype(np.float32)

    # Calculate Absolute Pixel Intensity Difference (0 to 255)
    abs_diff = np.abs(img_a_vals - img_b_vals)

    # Fill heatmap for visualization
    # We overlay all intersection diffs onto a single map
    diff_image = np.zeros((BEV_HEIGHT, BEV_WIDTH), dtype=np.float32)
    diff_image[overlap_mask] = abs_diff
    heat_map = np.maximum(heat_map, diff_image)

    # Metrics
    mae = np.mean(abs_diff)  # Mean Absolute Error
    rmse = np.sqrt(np.mean(abs_diff**2))  # Root Mean Squared Error

    all_maes.append(mae)

    print(
        f"Overlap: {cam_a: <9} | {cam_b: <9} ({num_overlapping_pixels: >6} px) -> MAE: {mae:.2f}/255.0, RMSE: {rmse:.2f}"
    )

overall_mae = np.mean(all_maes)
print("-" * 50)
print(f"OVERALL MEAN ABSOLUTE ERROR: {overall_mae:.2f}/255.0")
print("-" * 50)

# Save heatmap visualization
# Normalize 0-255 map linearly
heat_map_display = np.clip(heat_map, 0, 255).astype(np.uint8)

# Colorize it (Blue = 0 Error, Red = High Error)
heat_map_color = cv2.applyColorMap(heat_map_display, cv2.COLORMAP_JET)
# Mask it so only the actual overlapping boundaries show up
total_overlap_mask = np.zeros((BEV_HEIGHT, BEV_WIDTH), dtype=bool)
for cam_a, cam_b in pairs:
    total_overlap_mask |= camera_data[cam_a]["mask"] & camera_data[cam_b]["mask"]

heat_map_color[~total_overlap_mask] = (0, 0, 0)  # Black out non-overlaps

cv2.imwrite(os.path.join(debug_dir, "evaluation_error_heatmap.png"), heat_map_color)
print(f"Visual Error Heatmap saved to: data/bev_2d/debug/evaluation_error_heatmap.png")
