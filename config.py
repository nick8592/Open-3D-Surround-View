"""
config.py

Central configuration file for Open-3D-Surround-View.
Adjust these parameters to change the dimensions, resolution, or projection curves of your vehicle.
"""

# Intrinsic Calibration
INTRINSIC_CALIB_SQUARE_SIZE = 0.25 # Meters
INTRINSIC_CALIB_PATTERN_W = 7
INTRINSIC_CALIB_PATTERN_H = 7

# Extrinsic Calibration
EXTRINSIC_CALIB_SQUARE_SIZE = 0.25 # Meters (size of each square in the calibration pattern)
EXTRINSIC_CALIB_PATTERN_W = 7 # Number of inner corners along the width (X direction in image)
EXTRINSIC_CALIB_PATTERN_H = 5 # Number of inner corners along the height (Y direction in image)

CALIB_PAD_CENTER = { # Meters from the car center to the center of the calibration pad in the real world
    "Cam_Front": (3.5, 0), 
    "Cam_Back": (-3.5, 0),
    "Cam_Left": (0, 2),
    "Cam_Right": (0, -2),
}

# SVM Resolution and Scale
PIXELS_PER_METER = 100
BEV_WIDTH = 1000  # 10m x 10m area
BEV_HEIGHT = 1000

# Mapping Range (Physical Ground Coverage)
X_RANGE = (-5.0, 5.0)  # Meters (from bottom to top of image)
Y_RANGE = (-5.0, 5.0)  # Meters (from right to left of image)

# Car Dimensions (For UI Overlay and masking)
CAR_LENGTH = 4.8  # Meters
CAR_WIDTH = 1.9   # Meters
DRAW_CAR_MASK = False # Whether to draw the car mask bounding box over the final BEV map

# 3D Bowl Specific Parameters
BOWL_MAX_RADIUS = 4.8  # Tightly clip the 3D mesh to the valid camera coverage area
BOWL_NUM_RINGS = 40    # Mesh fidelity: How many concentric circles make up the bowl
BOWL_NUM_SLICES = 80   # Mesh fidelity: How many pie slices around the circle
BOWL_FLAT_RECT_X = 2.5 # Meters from origin: Defines width of the central rectangular "flat ground" zone
BOWL_FLAT_RECT_Y = 2.5 # Meters from origin: Defines length of the central rectangular "flat ground" zone
BOWL_FLAT_MARGIN = 1.5 # Meters of additional flat radial padding extending outward from the central rectangle before sweeping upward
BOWL_STEEPNESS = 0.5   # Exponent/Multiplier for how fast the edges curve upwards

# Projection Mask Tuning
MASK_RADIUS_SCALE = 1.05  # > 1.0 reduces masking on edges, letting camera see wider
