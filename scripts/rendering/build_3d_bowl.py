import numpy as np
import os

output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/rendering/3d_bowl"))
os.makedirs(output_dir, exist_ok=True)
obj_path = os.path.join(output_dir, "avm_pure_bowl.obj")

# ==========================================
# 3D Bowl Geometry Parameters
# ==========================================
MAX_RADIUS = 5.0      # The maximum radius of the bowl (10m diameter)
FLAT_RADIUS = 2.5     # The center flat area radius (Ground) where Z=0
BOWL_STEEPNESS = 0.5  # How steeply the edges curve upward

NUM_RINGS = 40        # Ring fidelity (How many concentric circles)
NUM_SLICES = 80       # Slice fidelity (How many pie slices around)

vertices = []

print("Generating perfectly smooth Polar 3D Bowl...")

# Generate the center vertex (Radius = 0)
# Automotive Standard ISO 8855: Origin (0,0,0) is center of rear axle on the ground.
# X points Forward, Y points Left, Z points Up.
vertices.append((0.0, 0.0, 0.0))

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
        # theta = 0 points Forward (+X)
        # theta = pi/2 points Left (+Y)
        theta = (s_idx / NUM_SLICES) * 2.0 * np.pi
        
        x = radius * np.cos(theta)
        y = radius * np.sin(theta)
        
        vertices.append((x, y, z))

print(f"Generated {len(vertices)} precise vertices.")

# Export to Wavefront .OBJ
with open(obj_path, "w") as f:
    f.write("o AVM_Pure_Bowl\n")
    
    # 1. Write all vertices
    for v in vertices:
        f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
        
    # 2. Write Faces (Connecting the dots)
    f.write("s 1\n") # Enable smooth shading
    
    # Center triangles connecting the origin (v=1) to the first ring
    for s_idx in range(NUM_SLICES):
        v0 = 1
        v1 = 2 + s_idx
        v2 = 2 + ((s_idx + 1) % NUM_SLICES)
        f.write(f"f {v0} {v1} {v2}\n")
        
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
            
            # Split quad into two triangles
            f.write(f"f {bl} {br} {tr}\n")
            f.write(f"f {bl} {tr} {tl}\n")

print(f"SUCCESS! Clean Geometry saved to: {obj_path}")
