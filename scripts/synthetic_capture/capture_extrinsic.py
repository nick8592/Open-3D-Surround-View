"""
Module: capture_extrinsic.py

This module provides functionality related to capture extrinsic.
"""

import os

import bpy


def main():
    # Determine project root (base_dir)
    if os.path.exists("/workspace"):
        base_dir = "/workspace"
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.abspath(os.path.join(script_dir, "../../"))

    # Auto-adapt path: use base_dir/scenes or fall back to /workspace/scenes
    scene_path = os.path.join(base_dir, "scenes", "svm_v1.blend")
    if not os.path.exists(scene_path):
        scene_path = "/workspace/scenes/svm_v1.blend"

    output_dir = os.path.join(base_dir, "data", "calibration", "extrinsic", "images")
    os.makedirs(output_dir, exist_ok=True)

    # 2. Open Blender scene file
    if os.path.exists(scene_path):
        print(f"Opening scene: {scene_path}")
        bpy.ops.wm.open_mainfile(filepath=scene_path)
    else:
        print(f"Error: Scene file not found at {scene_path}")
        return

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
