"""
Module: demo.py

Zero Friction Onboarding - Open-3D-Surround-View
Instantly generates a 2D BEV and a 3D Bowl render using the `data/sample/` dataset.
This script skips the calibration process by injecting the pre-calculated sample K/D and R/T matrices,
and runs the core AVM engine to rapidly produce outputs.
"""

import os
import shutil
import numpy as np
import cv2
import yaml
import subprocess

demo_dir = os.path.abspath(os.path.dirname(__file__))
base_dir = os.path.abspath(os.path.join(demo_dir, ".."))

# 1. Paths Setup
sample_dir = os.path.join(base_dir, "data/sample")
yaml_path = os.path.join(sample_dir, "calibration.yaml")

# Pipeline inputs
intr_dir = os.path.join(base_dir, "data/calibration/intrinsic/params")
extr_dir = os.path.join(base_dir, "data/calibration/extrinsic/params")
extr_img_dir = os.path.join(base_dir, "data/calibration/extrinsic/images")

os.makedirs(intr_dir, exist_ok=True)
os.makedirs(extr_dir, exist_ok=True)
os.makedirs(extr_img_dir, exist_ok=True)

# 2. Parse sample YAML and distribute arrays
if not os.path.exists(yaml_path):
    print("Error: data/sample/calibration.yaml not found!")
    exit(1)

with open(yaml_path, "r") as f:
    calib = yaml.safe_load(f)

print("Found Sample Dataset. Injecting Intrinsic Parameters...")
intr_npz_path = os.path.join(intr_dir, "intrinsic_params.npz")
K = np.array(calib["intrinsic"]["K"], dtype=np.float64)
D = np.array(calib["intrinsic"]["D"], dtype=np.float64)
np.savez_compressed(intr_npz_path, K=K, D=D)

# Update extrinsics
cams = {"front": "Cam_Front", "left": "Cam_Left", "rear": "Cam_Back", "right": "Cam_Right"}

for simple_name, full_name in cams.items():
    print(f"Injecting Extrinsic Parameters ({full_name})...")
    extr_npz_path = os.path.join(extr_dir, f"extrinsic_{full_name}.npz")
    rvec = np.array([calib["extrinsic"][simple_name]["rvec"]], dtype=np.float64).reshape(3, 1)
    tvec = np.array([calib["extrinsic"][simple_name]["tvec"]], dtype=np.float64).reshape(3, 1)
    # The AVM expects Eulerian R_matrix or pure rvec
    # We save exactly what the pipeline requires
    np.savez_compressed(extr_npz_path, rvec=rvec, tvec=tvec)
    
    # 3. Copy matching JPG to PNG in the extrinsic image folder
    src_img = os.path.join(sample_dir, f"{simple_name}.jpg")
    dst_img = os.path.join(extr_img_dir, f"{full_name}.png")
    if os.path.exists(src_img):
        img = cv2.imread(src_img)
        cv2.imwrite(dst_img, img)
    else:
        print(f"Error: Required sample image {src_img} not found.")

# 4. Run the Pipeline!
def run_script(script_path, interpreter="python3", extra_args=None):
    if extra_args is None:
        extra_args = []
    print(f"Executing {script_path}...")
    cmd = [interpreter] + extra_args + [os.path.join(base_dir, script_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to run {script_path}:\n{result.stderr}")

print("\nInjecting data into AVM engine...\n")

# Run 2D BEV Pipeline
run_script("scripts/bev_2d/stitching_bev.py")
run_script("scripts/bev_2d/render_bev.py")
shutil.copy(os.path.join(base_dir, "data/bev_2d/realtime_demo_bev.png"), os.path.join(demo_dir, "demo_bev.png"))
print("2D BEV Engine Complete! Exported: demo/demo_bev.png")

# Run 3D Bowl Pipeline
run_script("scripts/bowl_3d/build_bowl.py")
run_script("scripts/bowl_3d/stitching_bowl.py")
run_script("scripts/bowl_3d/render_bowl.py")
shutil.copy(os.path.join(base_dir, "data/bowl_3d/realtime_demo_bowl.png"), os.path.join(demo_dir, "demo_bowl.png"))
print("3D Bowl ECU Render Complete! Exported: demo/demo_bowl.png")

print("\nQuick Start Pipeline Complete. Please check the `demo/` folder.")
