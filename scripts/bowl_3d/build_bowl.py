"""
Module: build_bowl.py

This module provides functionality related to build bowl.
"""

import os

import numpy as np

output_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../data/bowl_3d")
)
os.makedirs(output_dir, exist_ok=True)
obj_path = os.path.join(output_dir, "avm_pure_bowl.obj")

# ==========================================
# 3D Bowl Geometry Parameters
# ==========================================
MAX_RADIUS = 4.8  # Tightly clip the mesh to the valid camera coverage area
FLAT_RADIUS = 2.5  # The center flat area radius (Ground) where Z=0
BOWL_STEEPNESS = 0.5  # How steeply the edges curve upward

NUM_RINGS = 40  # Ring fidelity (How many concentric circles)
NUM_SLICES = 80  # Slice fidelity (How many pie slices around)

vertices = []
uvs = []

print("Generating perfectly smooth Polar 3D Bowl...")

# Generate the center vertex (Radius = 0)
# Automotive Standard ISO 8855: Origin (0,0,0) is center of rear axle on the ground.
# X points Forward, Y points Left, Z points Up.
vertices.append((0.0, 0.0, 0.0))
# The center of the texture is exactly Center U=0.5, V=0.5
uvs.append((0.5, 0.5))

# Generate the Rings expanding outward
for r_idx in range(1, NUM_RINGS + 1):
    radius = (r_idx / NUM_RINGS) * MAX_RADIUS

    # Define the Z-Depth (Bowl Shape)
    if radius <= FLAT_RADIUS:
        z = 0.0
    else:
        # Parabolic curve upwards
        z = ((radius - FLAT_RADIUS) ** 2) * BOWL_STEEPNESS

    # Generate points around the ring
    for s_idx in range(NUM_SLICES):
        # Theta = 0 points Forward (+X)
        # Theta = pi/2 points Left (+Y)
        theta = (s_idx / NUM_SLICES) * 2.0 * np.pi

        x = radius * np.cos(theta)
        y = radius * np.sin(theta)

        vertices.append((x, y, z))

        # Calculate UV mapping strictly bound to our 10x10m 2D AVM rendering coordinates (Z=0 equivalent projection)
        # Because we used `Y = 5.0 - (u/100)`, U texture coord is exactly `(5.0 - Y) / 10.0`
        u_coord = (5.0 - y) / 10.0
        # Because we used `X = 5.0 - (v/100)`, image V is `(5.0 - X)/10.0`. OBJ V reverses direction -> `(5.0 + x) / 10.0`
        v_coord = (5.0 + x) / 10.0
        uvs.append((u_coord, v_coord))

print(f"Generated {len(vertices)} precise vertices with UV metrics.")

# Export Material MTL file
mtl_path = os.path.join(output_dir, "avm_pure_bowl.mtl")
with open(mtl_path, "w") as f:
    f.write("newmtl BowlTexture\n")
    f.write("Ka 1.000000 1.000000 1.000000\n")
    f.write("Kd 1.000000 1.000000 1.000000\n")
    f.write("map_Kd bowl_texture.png\n")

# Export to Wavefront .OBJ
with open(obj_path, "w") as f:
    f.write("mtllib avm_pure_bowl.mtl\n")
    f.write("o AVM_Pure_Bowl\n")

    # 1. Write all vertices
    for v in vertices:
        f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")

    # 2. Write all UVs
    for uv in uvs:
        f.write(f"vt {uv[0]:.6f} {uv[1]:.6f}\n")

    # 3. Write Faces (Connecting the dots)
    f.write("usemtl BowlTexture\n")
    f.write("s 1\n")  # Enable smooth shading

    # Center triangles connecting the origin (v=1) to the first ring
    for s_idx in range(NUM_SLICES):
        v0 = 1
        v1 = 2 + s_idx
        v2 = 2 + ((s_idx + 1) % NUM_SLICES)
        f.write(
            f"f {v0}/{v0} {v2}/{v2} {v1}/{v1}\n"
        )  # Blender reads counter-clockwise normals

    # Quads connecting the rest of the rings
    for r_idx in range(1, NUM_RINGS):
        ring_start = 2 + (r_idx - 1) * NUM_SLICES
        next_ring_start = 2 + r_idx * NUM_SLICES

        for s_idx in range(NUM_SLICES):
            curr_s = s_idx
            next_s = (s_idx + 1) % NUM_SLICES

            bl = ring_start + curr_s
            br = ring_start + next_s
            tl = next_ring_start + curr_s
            tr = next_ring_start + next_s

            # Split quad into two triangles (Counter-Clockwise relative to Z-Up normal vector)
            f.write(f"f {br}/{br} {tr}/{tr} {tl}/{tl}\n")
            f.write(f"f {bl}/{bl} {br}/{br} {tl}/{tl}\n")

print(f"SUCCESS! Clean UV-Mapped Geometry saved to: {obj_path}")
