import cv2
import numpy as np
import os
import sys
import time

PIXELS_PER_METER = 100
BEV_WIDTH = 1000
BEV_HEIGHT = 1000

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
luts_dir = os.path.join(base_dir, "data/rendering/3d_bowl/luts")
images_dir = os.path.join(base_dir, "data/calibration/extrinsic/images")

cameras = ["Cam_Front", "Cam_Left", "Cam_Back", "Cam_Right"]
luts = {}

print("Loading pre-computed 3D Bowl Look-Up Tables (LUTs)...")
for cam in cameras:
    lut_path = os.path.join(luts_dir, f"lut_bowl_{cam}.npz")
    if not os.path.exists(lut_path):
        print(f"Error: Missing LUT for {cam}. Run stitching_bowl.py first to generate them.")
        sys.exit(1)
        
    with np.load(lut_path) as data:
        # Pre-calculated projection coordinates based on Z-Up bowl
        map_x = data['map_x']
        map_y = data['map_y']
        # Pre-normalized alpha blending weight
        weight = data['weight']
        
        luts[cam] = {
            "map_x": map_x,
            "map_y": map_y,
            "weight": np.stack([weight]*3, axis=-1).astype(np.float32) 
        }

print("\nStarting simulated Real-Time 3D Bowl Render loop...")

frames = {}
for cam in cameras:
    frames[cam] = cv2.imread(os.path.join(images_dir, f"{cam}.png"))

def create_car_overlay():
    overlay = np.zeros((BEV_HEIGHT, BEV_WIDTH, 3), dtype=np.uint8)
    car_top = int(BEV_HEIGHT/2 - 2.4 * PIXELS_PER_METER)
    car_bot = int(BEV_HEIGHT/2 + 2.4 * PIXELS_PER_METER)
    car_left = int(BEV_WIDTH/2 - 0.9 * PIXELS_PER_METER)
    car_right = int(BEV_WIDTH/2 + 0.9 * PIXELS_PER_METER)
    
    cv2.rectangle(overlay, (car_left, car_top), (car_right, car_bot), (30, 30, 30), -1)
    cv2.rectangle(overlay, (car_left, car_top), (car_right, car_bot), (255, 255, 255), 3)
    cv2.putText(overlay, "CAR", (int(BEV_WIDTH/2 - 25), car_top + 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    return overlay

car_overlay = create_car_overlay()
car_mask = (car_overlay > 0)

# Simulate bounding limits
u, v = np.meshgrid(np.arange(BEV_WIDTH), np.arange(BEV_HEIGHT))
X = 5.0 - (v / PIXELS_PER_METER)
Y = 5.0 - (u / PIXELS_PER_METER)
R_abs = np.sqrt(X**2 + Y**2)

NUM_FRAMES = 50
start_time = time.time()

for i in range(NUM_FRAMES):
    # This loop runs constantly injecting 4 frames into a composed 3D Bowl Texture
    bev = np.zeros((BEV_HEIGHT, BEV_WIDTH, 3), dtype=np.float32)
    
    for cam in cameras:
        lut = luts[cam]
        img = frames[cam]
        
        # 1. Fetch pixels instantly correcting for curving 3D wall distortion
        warped = cv2.remap(img, lut["map_x"], lut["map_y"], cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0))
        
        # 2. Multiply by alpha weight and composite instantly (no 3D math required)
        bev += warped.astype(np.float32) * lut["weight"]
        
    final_bev = bev.astype(np.uint8)
    
    # Render UI Overlay
    final_bev[car_mask] = car_overlay[car_mask]
    
    # Clip alpha transparency
    final_bev_rgba = cv2.cvtColor(final_bev, cv2.COLOR_BGR2BGRA)
    final_bev_rgba[R_abs > 4.9] = (0,0,0,0)

end_time = time.time()
fps = NUM_FRAMES / (end_time - start_time)

print(f"Processed 4x Camera inputs to composite 1000x1000px 3D Bowl Texture.")
print(f"Performance: {fps:.2f} Frames Per Second (FPS) in Python")

output_path = os.path.join(base_dir, "data/rendering/3d_bowl/realtime_demo_bowl.png")
cv2.imwrite(output_path, final_bev_rgba)
print(f"Output saved to: {output_path}")
