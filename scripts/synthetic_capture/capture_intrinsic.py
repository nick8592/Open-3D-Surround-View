"""
Module: capture_intrinsic.py

This module provides functionality related to capture intrinsic.
"""

import math
import os

import bpy


def main():
    # Determine project root (base_dir)
    # Check if /workspace exists (Docker), otherwise use relative path from script
    if os.path.exists("/workspace"):
        base_dir = "/workspace"
    else:
        # Script is in scripts/simulation/, so project root is two levels up
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.abspath(os.path.join(script_dir, "../../"))

    output_dir = os.path.join(base_dir, "data", "calibration", "intrinsic", "images")
    os.makedirs(output_dir, exist_ok=True)

    # Try to find a suitable camera
    # 1. Search for "Camera"
    # 2. Search for "Cam_Front" (common in SVM)
    # 3. Fallback to the first available camera
    cam = bpy.data.objects.get("Camera")
    if not cam:
        cam = bpy.data.objects.get("Cam_Front")

    if not cam:
        all_cameras = [obj for obj in bpy.data.objects if obj.type == "CAMERA"]
        if all_cameras:
            cam = all_cameras[0]
            print(
                f"Warning: 'Camera' not found. Using first available camera: '{cam.name}'"
            )
        else:
            print("Error: No camera objects found in the scene.")
            print("Available objects:", [obj.name for obj in bpy.data.objects])
            return

    print(f"Using camera: {cam.name}")

    # Capture list: (Location XYZ, Rotation Euler in Radians)
    # The checkerboard is at (0, 0, 0)
    captures = [
        # --- Group A: Center & Height variations (3 images) ---
        ((0, 0, 2.0), (0, 0, 0)),  # High center
        ((0, 0, 1.5), (0, 0, 0)),  # Mid center
        ((0, 0, 1.0), (0, 0, 0)),  # Low center (Extreme zoom)
        # --- Group B: Radical Tilted Views (4 images) ---
        (
            (0.6, 0.6, 1.4),
            (math.radians(-25), math.radians(25), 0),
        ),  # Top-Right aggressive
        (
            (-0.6, -0.6, 1.4),
            (math.radians(25), math.radians(-25), 0),
        ),  # Bottom-Left aggressive
        (
            (0.6, -0.6, 1.4),
            (math.radians(25), math.radians(25), 0),
        ),  # Bottom-Right aggressive
        (
            (-0.6, 0.6, 1.4),
            (math.radians(-25), math.radians(-25), 0),
        ),  # Top-Left aggressive
        # --- Group C: Near-Edge Distortion Tests (4 images) ---
        ((1.2, 0, 1.2), (0, math.radians(45), 0)),  # Extreme Right
        ((-1.2, 0, 1.2), (0, math.radians(-45), 0)),  # Extreme Left
        ((0, 1.2, 1.2), (math.radians(-45), 0, 0)),  # Extreme Top
        ((0, -1.2, 1.2), (math.radians(45), 0, 0)),  # Extreme Bottom
        # --- Group D: Diagonal & Roll variations (4 images) ---
        (
            (0.8, 0.8, 1.6),
            (math.radians(-20), math.radians(20), math.radians(45)),
        ),  # Diagonal with Roll
        ((-0.8, 0.8, 1.6), (math.radians(-20), math.radians(-20), math.radians(-45))),
        ((0.8, -0.8, 1.6), (math.radians(20), math.radians(20), math.radians(-45))),
        ((0, 0, 1.8), (0, 0, math.radians(90))),  # Top-down with 90deg roll
    ]

    for i, (loc, rot) in enumerate(captures):
        cam.location = loc
        cam.rotation_euler = rot

        file_path = os.path.join(output_dir, f"intrinsic_calib_{i}.png")
        bpy.context.scene.render.filepath = file_path

        print(f"Rendering view {i}/{len(captures)-1}: Pos={loc}, Rot={rot}")
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
