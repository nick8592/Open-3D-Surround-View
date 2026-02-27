import cv2
import numpy as np
import os

def verify():
    # Determine project root (base_dir)
    if os.path.exists("/workspace/data/calibration"):
        base_dir = "/workspace"
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.abspath(os.path.join(script_dir, "../../"))

    img_path = os.path.join(base_dir, "data/calibration/intrinsic/images/planar_calib_0.png")
    if not os.path.exists(img_path):
        print(f"Error: Target image not found at {img_path}")
        return

    img = cv2.imread(img_path)
    h, w = img.shape[:2]

    # 1. Load calibrated intrinsic parameters
    params_path = os.path.join(base_dir, "data/calibration/intrinsic/params/intrinsic_params.npz")
    if not os.path.exists(params_path):
        print(f"Error: Calibration parameters not found at {params_path}")
        print("Please run calibrate_intrinsics.py first.")
        return

    with np.load(params_path) as data:
        K = data['K']
        D = data['D']
    
    print(f"Loaded parameters from {params_path}")

    # 2. Manually construct a new K, forcing a 1:1 aspect ratio and adjusting scale
    # We take the fx from calibrated K as the baseline and multiply by a scale factor
    scale = 0.5  # Smaller value = wider field of view; larger value = zoomed in
    new_f = K[0, 0] * scale

    new_K = np.array([
        [new_f, 0, w / 2],   # Center cx set to half of image width
        [0, new_f, h / 2],   # Center cy set to half of image height
        [0, 0, 1]
    ], dtype=np.float64)

    # 3. Perform undistortion
    map1, map2 = cv2.fisheye.initUndistortRectifyMap(K, D, np.eye(3), new_K, (w, h), cv2.CV_16SC2)
    undistorted_img = cv2.remap(img, map1, map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)

    output_path = os.path.join(base_dir, "data/calibration/intrinsic/debug/test_undistort.png")
    cv2.imwrite(output_path, undistorted_img)
    print(f"Undistorted image saved to: {output_path}")

if __name__ == "__main__":
    verify()