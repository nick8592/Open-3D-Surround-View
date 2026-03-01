"""
Module: render_bev.py

This module provides functionality related to render bev.
"""

import os
import sys
import time

import cv2
import numpy as np

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

if base_dir not in sys.path:
    sys.path.append(base_dir)

import config

PIXELS_PER_METER = config.PIXELS_PER_METER
BEV_WIDTH = config.BEV_WIDTH
BEV_HEIGHT = config.BEV_HEIGHT
CAR_LENGTH = config.CAR_LENGTH
CAR_WIDTH = config.CAR_WIDTH
luts_dir = os.path.join(base_dir, "data/bev_2d/luts")
images_dir = os.path.join(base_dir, "data/calibration/extrinsic/images")

cameras = ["Cam_Front", "Cam_Left", "Cam_Back", "Cam_Right"]
luts = {}

print("Loading pre-computed SVM Look-Up Tables (LUTs)...")
for cam in cameras:
    lut_path = os.path.join(luts_dir, f"lut_{cam}.npz")
    if not os.path.exists(lut_path):
        print(
            f"Error: Missing LUT for {cam}. Run stitching_bev.py first to generate them."
        )
        sys.exit(1)

    with np.load(lut_path) as data:
        # Pre-calculated projection coordinates
        map_x = data["map_x"]
        map_y = data["map_y"]
        # Pre-normalized alpha blending weight
        weight = data["weight"]

        luts[cam] = {
            "map_x": map_x,
            "map_y": map_y,
            # Expand weight to 3 channels for fast vectorized color multiplication
            "weight": np.stack([weight] * 3, axis=-1).astype(np.float32),
        }

print("\nStarting simulated Real-Time Render loop...")

# Load our static test images (In a real car, this would be a live VideoCapture feed)
frames = {}
for cam in cameras:
    frames[cam] = cv2.imread(os.path.join(images_dir, f"{cam}.png"))


# Pre-draw the Car Icon overlay
def create_car_overlay():
    overlay = np.zeros((BEV_HEIGHT, BEV_WIDTH, 3), dtype=np.uint8)
    car_top = int(BEV_HEIGHT / 2 - (CAR_LENGTH / 2.0) * PIXELS_PER_METER)
    car_bot = int(BEV_HEIGHT / 2 + (CAR_LENGTH / 2.0) * PIXELS_PER_METER)
    car_left = int(BEV_WIDTH / 2 - (CAR_WIDTH / 2.0) * PIXELS_PER_METER)
    car_right = int(BEV_WIDTH / 2 + (CAR_WIDTH / 2.0) * PIXELS_PER_METER)

    cv2.rectangle(overlay, (car_left, car_top), (car_right, car_bot), (30, 30, 30), -1)
    cv2.rectangle(
        overlay, (car_left, car_top), (car_right, car_bot), (255, 255, 255), 3
    )
    cv2.putText(
        overlay,
        "FRONT",
        (int(BEV_WIDTH / 2 - 40), car_top + 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
    )
    return overlay


car_overlay = create_car_overlay()
car_mask = car_overlay > 0

# Simulate 50 frames to measure FPS
NUM_FRAMES = 50
start_time = time.time()

for i in range(NUM_FRAMES):
    # This loop represents what happens EVERY SINGLE FRAME in a real car dashboard
    bev = np.zeros((BEV_HEIGHT, BEV_WIDTH, 3), dtype=np.float32)

    for cam in cameras:
        lut = luts[cam]
        img = frames[cam]

        # 1. Fetch exact pixel colors instantly mapping curved 180 FOV to flat ground
        warped = cv2.remap(
            img,
            lut["map_x"],
            lut["map_y"],
            cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0),
        )

        # 2. Multiply by alpha weight and composite instantly (no complex math)
        bev += warped.astype(np.float32) * lut["weight"]

    final_bev = bev.astype(np.uint8)

    # Render UI Overlay
    final_bev[car_mask] = car_overlay[car_mask]

end_time = time.time()
fps = NUM_FRAMES / (end_time - start_time)

print(f"Processed 4x Camera inputs to composite 1000x1000px SVM output.")
print(f"Performance: {fps:.2f} Frames Per Second (FPS) in Python")

output_path = os.path.join(base_dir, "data/bev_2d/realtime_demo_bev.png")
cv2.imwrite(output_path, final_bev)
print(f"Output saved to: {output_path}")
