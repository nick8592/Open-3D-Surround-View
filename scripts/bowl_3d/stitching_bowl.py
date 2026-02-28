import os
import sys

import cv2
import numpy as np

# Define 3D Bowl mapping parameters
PIXELS_PER_METER = 100
BEV_WIDTH = 1000  # 10m x 10m area
BEV_HEIGHT = 1000
X_RANGE = (-5.0, 5.0)  # meters
Y_RANGE = (-5.0, 5.0)  # meters

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
intrinsic_params_path = os.path.join(
    base_dir, "data/calibration/intrinsic/params/intrinsic_params.npz"
)
extrinsic_dir = os.path.join(base_dir, "data/calibration/extrinsic/params")
images_dir = os.path.join(base_dir, "data/calibration/extrinsic/images")

output_dir = os.path.join(base_dir, "data/bowl_3d")
luts_dir = os.path.join(output_dir, "luts")
os.makedirs(output_dir, exist_ok=True)
os.makedirs(luts_dir, exist_ok=True)

# Load intrinsics
if not os.path.exists(intrinsic_params_path):
    print(f"Error: Intrinsic parameters not found at {intrinsic_params_path}")
    sys.exit(1)

with np.load(intrinsic_params_path) as data:
    K = data["K"]
    D = data["D"]

cameras = ["Cam_Front", "Cam_Left", "Cam_Back", "Cam_Right"]

print("Initializing 3D spatial mapping grid for 3D BOWL...")
u, v = np.meshgrid(np.arange(BEV_WIDTH), np.arange(BEV_HEIGHT))

# In automotive standard (X forward, Y left):
X = X_RANGE[1] - (v / PIXELS_PER_METER)
Y = Y_RANGE[1] - (u / PIXELS_PER_METER)

# 1. Rounded Rectangle Flat Area to prevent parallax ghosting on the flat mats.
dx = np.maximum(np.abs(X) - 2.5, 0.0)
dy = np.maximum(np.abs(Y) - 1.5, 0.0)
R_dist = np.sqrt(dx**2 + dy**2)

# Bowl Depth Geometry (Z-up Curve)
FLAT_MARGIN = 1.5
BOWL_STEEPNESS = 0.5
Z = np.where(R_dist <= FLAT_MARGIN, 0.0, ((R_dist - FLAT_MARGIN) ** 2) * BOWL_STEEPNESS)

pts_3d = np.stack((X, Y, Z), axis=-1).reshape(-1, 1, 3).astype(np.float32)

bev_image_float = np.zeros((BEV_HEIGHT, BEV_WIDTH, 3), dtype=np.float32)
blend_weights = np.zeros((BEV_HEIGHT, BEV_WIDTH), dtype=np.float32)

camera_maps = {}  # Dictionary to store data for LUTs

print("\nProcessing cameras for 3D Bowl texture mapping:")
for cam in cameras:
    ext_path = os.path.join(extrinsic_dir, f"extrinsic_{cam}.npz")
    img_path = os.path.join(images_dir, f"{cam}.png")

    if not os.path.exists(ext_path) or not os.path.exists(img_path):
        print(f"  [Skip] {cam} (Missing data files)")
        continue

    with np.load(ext_path) as edata:
        rvec = edata["rvec"]
        tvec = edata["tvec"]

    img = cv2.imread(img_path)
    img_h, img_w = img.shape[:2]
    print(f"  [Procesing] {cam}: Projecting pure 3D Bowl logic...")

    # 1. Transform World to Camera coordinate to cull points behind the lens
    R, _ = cv2.Rodrigues(rvec)
    pts_3d_squeezed = pts_3d.reshape(-1, 3).T
    pts_cam = R @ pts_3d_squeezed + tvec
    z_cam = pts_cam[2, :].reshape(BEV_HEIGHT, BEV_WIDTH)

    # 2. Project 3D points onto the camera's 2D image plane using K and D
    pts_2d, _ = cv2.fisheye.projectPoints(pts_3d, rvec, tvec, K, D)
    pts_2d = pts_2d.reshape(BEV_HEIGHT, BEV_WIDTH, 2)

    map_x = pts_2d[..., 0].astype(np.float32)
    map_y = pts_2d[..., 1].astype(np.float32)

    # 3. Pull colors from original images based on mapping for the static preview
    warped = cv2.remap(
        img,
        map_x,
        map_y,
        cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0),
    )

    # 4. Generate Spatial Blend Weighting Mask
    z_mask = z_cam > 0
    valid_x = (map_x >= 0) & (map_x < img_w - 1)
    valid_y = (map_y >= 0) & (map_y < img_h - 1)

    radial_dist = np.sqrt((map_x - img_w / 2.0) ** 2 + (map_y - img_h / 2.0) ** 2) / (
        np.min([img_w, img_h]) / 2.0
    )
    weight = np.clip(1.0 - radial_dist, 0.0, 1.0)

    valid_mask = z_mask & valid_x & valid_y
    car_mask = (X > -2.4) & (X < 2.4) & (Y > -0.9) & (Y < 0.9)
    valid_mask = valid_mask & (~car_mask)

    weight = weight * valid_mask.astype(np.float32)

    # 5. Accumulate colors
    for c in range(3):
        bev_image_float[..., c] += warped[..., c].astype(np.float32) * weight
    blend_weights += weight

    # Store parameters for LUT generation
    camera_maps[cam] = {"map_x": map_x, "map_y": map_y, "weight": weight}

print("\nFinalizing stitching overlap logic...")
valid_pixels = blend_weights > 0
for c in range(3):
    bev_image_float[..., c][valid_pixels] /= blend_weights[valid_pixels]

bev_image = np.clip(bev_image_float, 0, 255).astype(np.uint8)

print("\nGenerating and saving optimized LUTs for Real-Time 3D Texture rendering...")
# Pre-divide the weights here so the real-time render loop avoids floating point division
safe_blend_weights = np.maximum(blend_weights, 1e-6)

for cam, maps in camera_maps.items():
    norm_weight = maps["weight"] / safe_blend_weights
    norm_weight[maps["weight"] == 0] = 0.0

    lut_path = os.path.join(luts_dir, f"lut_bowl_{cam}.npz")
    np.savez_compressed(
        lut_path, map_x=maps["map_x"], map_y=maps["map_y"], weight=norm_weight
    )
    print(f"  Saved 3D Bowl LUT -> {lut_path}")

# Central Car Icon
car_top = int(BEV_HEIGHT / 2 - 2.4 * PIXELS_PER_METER)
car_bot = int(BEV_HEIGHT / 2 + 2.4 * PIXELS_PER_METER)
car_left = int(BEV_WIDTH / 2 - 0.9 * PIXELS_PER_METER)
car_right = int(BEV_WIDTH / 2 + 0.9 * PIXELS_PER_METER)

cv2.rectangle(bev_image, (car_left, car_top), (car_right, car_bot), (30, 30, 30), -1)
cv2.rectangle(bev_image, (car_left, car_top), (car_right, car_bot), (255, 255, 255), 3)
cv2.putText(
    bev_image,
    "CAR",
    (int(BEV_WIDTH / 2 - 25), car_top + 40),
    cv2.FONT_HERSHEY_SIMPLEX,
    0.8,
    (255, 255, 255),
    2,
)

output_path = os.path.join(output_dir, "bowl_texture.png")
cv2.imwrite(output_path, bev_image)
print(
    f"\nSUCCESS: Stunning 3D Bowl Texture successfully rendered and mapped to {output_path}"
)
