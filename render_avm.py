import bpy
import os

# Get the absolute path of the directory where the script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Auto-adapt path: use /workspace if it exists, otherwise use the script's directory
scene_path = os.path.join(BASE_DIR, "scenes", "avm_v1.blend")
output_dir = os.path.join(BASE_DIR, "data", "render_output")

os.makedirs(output_dir, exist_ok=True)

# 2. Open Blender scene file
if os.path.exists(scene_path):
    bpy.ops.wm.open_mainfile(filepath=scene_path)
else:
    print(f"Error: Scene file not found {scene_path}")
    exit()

# 3. Define camera list
cameras = ["Cam_Front", "Cam_Back", "Cam_Left", "Cam_Right"]

# 4. Loop through and render
for cam_name in cameras:
    if cam_name in bpy.data.objects:
        bpy.context.scene.camera = bpy.data.objects[cam_name]
        
        file_path = os.path.join(output_dir, f"{cam_name}.jpg")
        bpy.context.scene.render.filepath = file_path
        
        print(f"Rendering {cam_name}...")
        bpy.ops.render.render(write_still=True)
        print(f"Saved to: {file_path}")
    else:
        print(f"Warning: Camera {cam_name} not found")

print("Four-way surround view rendering complete!")