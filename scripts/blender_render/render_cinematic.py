import bpy
import os
import math

# Paths
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
obj_path = os.path.join(base_dir, "data/bowl_3d/svm_pure_bowl.obj")
texture_path = os.path.join(base_dir, "data/bowl_3d/bowl_texture.png")
output_path = os.path.join(base_dir, "data/bowl_3d/cinematic_demo.mp4")

# 1. Clean up existing scene (delete all objects)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 2. Import the 3D Bowl OBJ
# Enforce the same axes as the mathematically generated ISO 8855 standard (Z-Up, X-Forward)
bpy.ops.import_scene.obj(filepath=obj_path, axis_forward='X', axis_up='Z')

# Select the imported bowl
bowl_obj = None
for obj in bpy.context.scene.objects:
    if "svm_pure_bowl" in obj.name or "SVM_Pure_Bowl" in obj.name:
        bowl_obj = obj
        break

if bowl_obj is None:
    # Fallback to the first imported object if name varies
    bowl_obj = bpy.context.selected_objects[0] if bpy.context.selected_objects else None

if not bowl_obj:
    print("Error: Could not find imported bowl object")
    exit()

# 3. Setup Material (Make it Emissive/Shadeless so it looks like a screen)
mat = bowl_obj.data.materials[0] if bowl_obj.data.materials else bpy.data.materials.new(name="BowlScreen")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links

for node in nodes:
    nodes.remove(node)

# Create highly emissive shader setup (like a dashboard screen)
tex_image = nodes.new('ShaderNodeTexImage')
tex_image.image = bpy.data.images.load(texture_path)

emission = nodes.new('ShaderNodeEmission')
emission.inputs['Strength'].default_value = 1.2

output = nodes.new('ShaderNodeOutputMaterial')

links.new(tex_image.outputs['Color'], emission.inputs['Color'])
links.new(emission.outputs['Emission'], output.inputs['Surface'])

if not bowl_obj.data.materials:
    bowl_obj.data.materials.append(mat)

# 4. Setup Lighting and Environment
bpy.context.scene.world.use_nodes = True
bg_node = bpy.context.scene.world.node_tree.nodes.get('Background')
if bg_node:
    bg_node.inputs[0].default_value = (0.01, 0.01, 0.01, 1) # Pitch black background

# 5. Create Camera and Empty for Turntable animation
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
focus_empty = bpy.context.active_object
focus_empty.name = "TurntableFocus"

# Start further behind the car (-X) looking forward
bpy.ops.object.camera_add(location=(-12.0, 0.0, 9.0))
cam = bpy.context.active_object
cam.name = "CinematicCamera"
cam.data.lens = 30  # Wider FOV

# Rotate camera to look perfectly at the center point
dir_vec = focus_empty.location - cam.location
cam.rotation_euler = dir_vec.to_track_quat('-Z', 'Y').to_euler()

# Parent camera to empty
cam.parent = focus_empty

bpy.context.scene.camera = cam

# 6. Animate the Turntable!
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 288 # 12 seconds at 24 fps
bpy.context.scene.render.fps = 24

# Frame 1: 0 degrees
focus_empty.rotation_euler[2] = 0
focus_empty.keyframe_insert(data_path="rotation_euler", index=2, frame=1)

# Frame 288: 360 degrees (2*pi radians)
focus_empty.rotation_euler[2] = 2 * math.pi
focus_empty.keyframe_insert(data_path="rotation_euler", index=2, frame=289) # Loop seamlessly

# Optional: Add subtle Z-height bobbing (like pushing into the car and pulling out)
cam.location = (-12.0, 0.0, 9.0)
cam.keyframe_insert(data_path="location", frame=1)
cam.location = (-4.0, 0.0, 2.5)
cam.keyframe_insert(data_path="location", frame=144)
cam.location = (-12.0, 0.0, 9.0)
cam.keyframe_insert(data_path="location", frame=289)

# Smooth interpolation (Linear for spin to loop perfectly, Bezier for height bobbing)
for fcurve in focus_empty.animation_data.action.fcurves:
    for kf in fcurve.keyframe_points:
        kf.interpolation = 'LINEAR'

# 7. Render Settings
bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.eevee.taa_render_samples = 16 # Low sample count for fast CPU rendering
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 720
bpy.context.scene.render.filepath = output_path
bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
bpy.context.scene.render.ffmpeg.format = 'MPEG4'
bpy.context.scene.render.ffmpeg.codec = 'H264'
bpy.context.scene.render.ffmpeg.constant_rate_factor = 'HIGH'

print(f"Starting cinematic batch render...")
bpy.ops.render.render(animation=True)
print(f"Render completed! File saved to: {output_path}")
