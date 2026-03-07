"""
Module: capture_extrinsic.py

This module provides functionality related to capture extrinsic.
"""

import os
import sys

import bpy


def main():
    # Determine project root (base_dir)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.abspath(os.path.join(script_dir, "../../"))

    output_dir = os.path.join(base_dir, "data", "calibration", "extrinsic", "images")
    os.makedirs(output_dir, exist_ok=True)

    # 2. Check if a scene file is loaded
    if not bpy.data.filepath:
        print("Error: No Blender scene file loaded.")
        print("Please specify a scene file when running the script:")
        print("  blender -b scenes/<scene_name>.blend -P scripts/synthetic_capture/capture_extrinsic.py")
        sys.exit(1)

    # 3. Define camera list
    cameras = ["Cam_Front", "Cam_Back", "Cam_Left", "Cam_Right"]

    # 4. Loop through and render
    for cam_name in cameras:
        if cam_name in bpy.data.objects:
            bpy.context.scene.camera = bpy.data.objects[cam_name]

            file_path = os.path.join(output_dir, f"{cam_name}.png")
            bpy.context.scene.render.filepath = file_path

            print(f"Rendering {cam_name}...")
            bpy.ops.render.render(write_still=True)
            print(f"Saved to: {file_path}")
        else:
            print(f"Warning: Camera {cam_name} not found in scene")

    print("Four-way surround view rendering complete!")


if __name__ == "__main__":
    main()
