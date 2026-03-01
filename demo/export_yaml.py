import os
import yaml
import numpy as np
import cv2

demo_dir = os.path.abspath(os.path.dirname(__file__))
base_dir = os.path.abspath(os.path.join(demo_dir, ".."))
# Load intrinsic
intr = np.load(os.path.join(base_dir, "data/calibration/intrinsic/params/intrinsic_params.npz"))
K = intr["K"].tolist()
D = intr["D"].tolist()

cams = {
    "front": "Cam_Front",
    "back": "Cam_Back",
    "left": "Cam_Left",
    "right": "Cam_Right"
}

yaml_data = {
    "intrinsic": {
        "K": K,
        "D": D
    },
    "extrinsic": {}
}

for simple_name, full_name in cams.items():
    extr_path = os.path.join(base_dir, f"data/calibration/extrinsic/params/extrinsic_{full_name}.npz")
    extr = np.load(extr_path)
    yaml_data["extrinsic"][simple_name] = {
        "rvec": extr["rvec"].tolist(),
        "tvec": extr["tvec"].tolist()
    }

os.makedirs(os.path.join(base_dir, "data/sample"), exist_ok=True)
with open(os.path.join(base_dir, "data/sample/calibration.yaml"), 'w') as f:
    yaml.dump(yaml_data, f, default_flow_style=None)

# copy images as jpg
for simple_name, full_name in cams.items():
    img_path = os.path.join(base_dir, f"data/calibration/extrinsic/images/{full_name}.png")
    img = cv2.imread(img_path)
    # Resize to something lighter for the sample dataset? Or keep full res?
    # Keeping 1920x1080 full res is fine, as jpg it will be ~200kb
    out_path = os.path.join(base_dir, f"data/sample/{simple_name}.jpg")
    cv2.imwrite(out_path, img, [cv2.IMWRITE_JPEG_QUALITY, 90])

print("Sample dataset exported!")
