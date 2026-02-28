import cv2
import numpy as np
import os
import sys

# Define BEV (Bird's-Eye View) mapping parameters
PIXELS_PER_METER = 100
BEV_WIDTH = 1000  # 10m x 10m area
BEV_HEIGHT = 1000 
X_RANGE = (-5.0, 5.0)  # meters (from bottom to top of image)
Y_RANGE = (-5.0, 5.0)  # meters (from right to left of image)

# Paths
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
intrinsic_params_path = os.path.join(base_dir, "data/calibration/intrinsic/params/intrinsic_params.npz")
extrinsic_dir = os.path.join(base_dir, "data/calibration/extrinsic/params")
images_dir = os.path.join(base_dir, "data/calibration/extrinsic/images")
output_dir = os.path.join(base_dir, "data/stitching")
debug_dir = os.path.join(output_dir, "debug")
os.makedirs(output_dir, exist_ok=True)
os.makedirs(debug_dir, exist_ok=True)

# Load intrinsics
if not os.path.exists(intrinsic_params_path):
    print(f"Error: Intrinsic parameters not found at {intrinsic_params_path}")
    sys.exit(1)

with np.load(intrinsic_params_path) as data:
    K = data['K']
    D = data['D']

cameras = ["Cam_Front", "Cam_Left", "Cam_Back", "Cam_Right"]

# Generate 3D grid corresponding to pixels on the BEV plane (Z=0)
print("Initializing 3D spatial mapping grid...")
u, v = np.meshgrid(np.arange(BEV_WIDTH), np.arange(BEV_HEIGHT))

# In automotive standard (X forward, Y left):
# v (row 0) is top of image -> max X (+5m).
# u (col 0) is left of image -> max Y (+5m).
X = X_RANGE[1] - (v / PIXELS_PER_METER)
Y = Y_RANGE[1] - (u / PIXELS_PER_METER)
Z = np.zeros_like(X)

pts_3d = np.stack((X, Y, Z), axis=-1).reshape(-1, 1, 3).astype(np.float32)

bev_image_float = np.zeros((BEV_HEIGHT, BEV_WIDTH, 3), dtype=np.float32)
blend_weights = np.zeros((BEV_HEIGHT, BEV_WIDTH), dtype=np.float32)

print("\nProcessing cameras for AVM stitching:")
for cam in cameras:
    ext_path = os.path.join(extrinsic_dir, f"extrinsic_{cam}.npz")
    img_path = os.path.join(images_dir, f"{cam}.png")
    
    if not os.path.exists(ext_path) or not os.path.exists(img_path):
        print(f"  [Skip] {cam} (Missing data files)")
        continue
        
    with np.load(ext_path) as edata:
        rvec = edata['rvec']
        tvec = edata['tvec']
        
    img = cv2.imread(img_path)
    img_h, img_w = img.shape[:2]
    print(f"  [Procesing] {cam}: Mapping pixels...")
    
    # 1. Transform World to Camera coordinate to cull points behind the lens
    R, _ = cv2.Rodrigues(rvec)
    pts_3d_squeezed = pts_3d.reshape(-1, 3).T      # 3 x N
    pts_cam = R @ pts_3d_squeezed + tvec           # 3 x N
    z_cam = pts_cam[2, :].reshape(BEV_HEIGHT, BEV_WIDTH)
    
    # 2. Project 3D points onto the camera's 2D image plane
    pts_2d, _ = cv2.fisheye.projectPoints(pts_3d, rvec, tvec, K, D)
    pts_2d = pts_2d.reshape(BEV_HEIGHT, BEV_WIDTH, 2)
    
    map_x = pts_2d[..., 0].astype(np.float32)
    map_y = pts_2d[..., 1].astype(np.float32)
    
    # 3. Pull colors from original images based on mapping
    warped = cv2.remap(img, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0))
    
    # 4. Generate Spatial Blend Weighting Mask
    # Mask out pixels that are physically behind the camera
    z_mask = (z_cam > 0)
    
    # Mask out points mapping entirely off the physical sensor
    valid_x = (map_x >= 0) & (map_x < img_w - 1)
    valid_y = (map_y >= 0) & (map_y < img_h - 1)
    
    # Define a smooth feathering weight based on distance from sensor center
    # This prevents harsh seams between overlapping fields of view
    # Distance normalized so center = 0, edge = 1
    radial_dist = np.sqrt((map_x - img_w / 2.0)**2 + (map_y - img_h / 2.0)**2) / (np.min([img_w, img_h]) / 2.0)
    weight = np.clip(1.0 - radial_dist, 0.0, 1.0)
    
    # Enforce boolean exclusions
    valid_mask = z_mask & valid_x & valid_y
    # Remove pixels that mapped inside the literal car bounding box footprint
    car_mask = (X > -2.4) & (X < 2.4) & (Y > -0.9) & (Y < 0.9)
    valid_mask = valid_mask & (~car_mask)
    
    weight = weight * valid_mask.astype(np.float32)
    
    # --- DEBUG SAVING ---
    # 1. Undistorted camera view
    # Extreme fisheye lenses (~180 FOV) mathematically stretch to infinity on flat pinhole projections.
    # OpenCV's auto-estimator pushes those edges to pure white/black. We scale the focal lengths artificially 
    # (e.g., * 0.5) to shrink the infinite projection into a visible cropped circle for debugging.
    scale = 0.5
    new_K = K.copy()
    new_K[0,0] = K[0,0] * scale
    new_K[1,1] = K[1,1] * scale
    
    # Use initUndistortRectifyMap + remap for performance standard consistency
    map1, map2 = cv2.fisheye.initUndistortRectifyMap(K, D, np.eye(3), new_K, (img_w, img_h), cv2.CV_16SC2)
    undistorted_img = cv2.remap(img, map1, map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    cv2.imwrite(os.path.join(debug_dir, f"{cam}_01_undistorted.png"), undistorted_img)
    
    # 2. View projected on BEV plane
    cv2.imwrite(os.path.join(debug_dir, f"{cam}_02_project_bev.png"), warped)
    
    # 3. Mask before weight
    cv2.imwrite(os.path.join(debug_dir, f"{cam}_03_mask_before_weight.png"), (valid_mask * 255).astype(np.uint8))
    
    # 4. Mask after weight
    cv2.imwrite(os.path.join(debug_dir, f"{cam}_04_mask_after_weight.png"), (weight * 255).astype(np.uint8))
    
    # 5. Weighted mask applied and project on BEV plane
    weighted_warped = (warped.astype(np.float32) * weight[..., np.newaxis]).astype(np.uint8)
    cv2.imwrite(os.path.join(debug_dir, f"{cam}_05_weighted_project_bev.png"), weighted_warped)
    # --------------------
    
    # 5. Accumulate colors
    for c in range(3):
        bev_image_float[..., c] += warped[..., c].astype(np.float32) * weight
    blend_weights += weight

print("\nFinalizing stitching overlap logic...")
valid_pixels = blend_weights > 0
for c in range(3):
    bev_image_float[..., c][valid_pixels] /= blend_weights[valid_pixels]

bev_image = np.clip(bev_image_float, 0, 255).astype(np.uint8)

# 6. Render the Central Car Icon properly oriented
# Vehicle is 4.8m long (-2.4 to +2.4) and 1.8m wide (-0.9 to +0.9)
car_top_pixels = int(BEV_HEIGHT/2 - 2.4 * PIXELS_PER_METER)
car_bottom_pixels = int(BEV_HEIGHT/2 + 2.4 * PIXELS_PER_METER)
car_left_pixels = int(BEV_WIDTH/2 - 0.9 * PIXELS_PER_METER)
car_right_pixels = int(BEV_WIDTH/2 + 0.9 * PIXELS_PER_METER)

cv2.rectangle(bev_image, (car_left_pixels, car_top_pixels), (car_right_pixels, car_bottom_pixels), (30, 30, 30), -1)
cv2.rectangle(bev_image, (car_left_pixels, car_top_pixels), (car_right_pixels, car_bottom_pixels), (255, 255, 255), 3)
cv2.putText(bev_image, "FRONT", (int(BEV_WIDTH/2 - 40), car_top_pixels + 40), 
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

output_path = os.path.join(output_dir, "bev.png")
cv2.imwrite(output_path, bev_image)
print(f"\nSUCCESS: Stunning 2D Bird's-Eye View successfully rendered and mapped to {output_path}")
