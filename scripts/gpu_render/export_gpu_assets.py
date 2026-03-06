import cv2
import numpy as np
import os
import sys

# Script to transform generated 3D LUT arrays and alpha masks into GPU-friendly textures (like raw binary floats)

# Assuming fisheye source resolution. In production, read this dynamically from calibration or config
FISHEYE_WIDTH = 1920.0
FISHEYE_HEIGHT = 1536.0

def main():
    print("Exporting assets for GPU renderer...")
    luts_dir = os.path.join("data", "bowl_3d", "luts")
    output_dir = os.path.join("data", "gpu_assets")
    os.makedirs(output_dir, exist_ok=True)

    cameras = ['Front', 'Back', 'Left', 'Right']
    weights = []

    for cam in cameras:
        npz_path = os.path.join(luts_dir, f"lut_bowl_Cam_{cam}.npz")
        
        if not os.path.exists(npz_path):
            print(f"Error: Could not find {npz_path}! Did you run the CPU stitching pipeline first?")
            return

        print(f"Processing {cam} camera data...")
        data = np.load(npz_path)
        map_x = data['map_x']
        map_y = data['map_y']
        weight = data['weight']

        # 1. Normalize Pixel Coordinates to UV (0.0 - 1.0)
        uv_u = (map_x / FISHEYE_WIDTH).astype(np.float32)
        uv_v = (map_y / FISHEYE_HEIGHT).astype(np.float32)

        # Build a 2-channel Float32 image (RG16F or RG32F)
        lut_texture = np.dstack((uv_u, uv_v))
        
        # Save as raw binary for C++/OpenGL to read directly via glBufferData or glTexImage2D
        out_lut = os.path.join(output_dir, f"lut_{cam}.bin")
        lut_texture.tofile(out_lut)

        weights.append(weight.astype(np.float32))

    # 2. Combine weights into an RGBA texture for the blend mask
    print("Combining alpha masks into RGBA blend texture...")
    blend_mask = np.dstack((
        weights[0], # R = Front
        weights[1], # G = Back
        weights[2], # B = Left
        weights[3]  # A = Right
    ))
    
    out_blend = os.path.join(output_dir, "blend_mask.bin")
    blend_mask.tofile(out_blend)

    # Save meta info (like resolution) to help the C++/Python GPU renderer know the shape
    with open(os.path.join(output_dir, "meta.txt"), "w") as f:
        f.write(f"LUT_WIDTH={blend_mask.shape[1]}\n")
        f.write(f"LUT_HEIGHT={blend_mask.shape[0]}\n")

    print(f"Done! GPU binary assets saved to {output_dir}")

if __name__ == "__main__":
    main()
