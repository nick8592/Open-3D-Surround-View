import bpy
import os

# Clear default cube and lights
bpy.ops.wm.read_factory_settings(use_empty=True)

# Set absolute path for the generated 3D model
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.abspath(os.path.join(script_dir, "../../"))
obj_path = os.path.join(base_dir, "data/rendering/3d_bowl/avm_pure_bowl.obj")

# Import OBJ (Automatically loads MTL and Textures)
# CRITICAL: Blender's OBJ Importer defaults to Y-Up (like Maya), meaning it will automatically rotate Z-Up files 90 degrees!
# We must explicitly enforce axis_up='Z' to preserve our ISO 8855 automotive standard rotations.
bpy.ops.import_scene.obj(filepath=obj_path, axis_forward='Y', axis_up='Z')

# Switch viewport to Wireframe mode for precise geometric and topological review
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'SOLID'
                space.shading.show_wire = True 

print("✅ Pure 3D Bowl imported successfully for geometry review!")
