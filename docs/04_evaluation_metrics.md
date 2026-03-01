# SVM Evaluation Metrics (Proving Calibration Goodness)

Because fisheye distortion and 3D space are hard to perfectly "eyeball," we designed three mathematical pillars inside our `/scripts/calibration` and `/scripts/bev_2d` codebase to categorically evaluate the *goodness* of the calibration.

## 1. Intrinsic Goodness: RMS Reprojection Error & Plumb-Line Curvature
During the initial extraction of lens physics in `calibrate_intrinsic.py`, OpenCV runs an internal feedback loop. 
After approximating the focal length (`K`) and distortion (`D`) curves of the lens, OpenCV forces the computer to re-draw the 3D calibration chessboard on a flat 2D image pixel plane using those mathematical parameters.
It then measures the exact sub-pixel distance between where OpenCV *thought* the checkerboard corner should be, against where it *actually* detected the corner in the raw photo.

If this **Root Mean Square (RMS) Error** averages under 1.0 pixels, the intrinsic formula correctly reverses the lens distortion.
A secondary validation is built in `evaluate_intrinsic.py` using **Plumb-Line Variance (Straightness)**. It takes the undistorted image, finds the corners again, runs them through a linear regression fit, and calculates their exact perpendicular drift to confirm that all straight-lines in the real world look completely rigid and straight on the screen.

## 2. Extrinsic Goodness: 3D-to-2D Reprojection Distance
In `evaluate_extrinsic.py`, we take the final physical position (Z-Height, Pitch, Roll) of the cameras mounted to the car model and run the ultimate alignment check.

We feed the ISO 8855 World Coordinate System physical matrix (e.g. `X=3.5, Y=2.0, Z=0.0` points where the calibration mat sat in front of the car) backwards into our fisheye math model.
We predict exactly which 2D Pixel `X, Y` on the camera image should map to that physical mat.
Then, we literally search the raw image of the mat itself for its high-contrast corners.

The **Mean Sub-pixel Reprojection Error** measures the difference between our ISO 8855 prediction and the actual photograph. If the camera was accidentally pitched downward even 1-degree off our calculations, the error would spike massively. When the error is ~0.03 pixels, we know we perfectly mapped the physical world.

## 3. Stitching Goodness: Photometric Overlap Alignment (MAE)
The hardest thing to physically evaluate in a Surround View setup is the final stitching output across the 4 corners of the car.

Because the Front Camera and Left Camera physically share the "Front-Left Ground Corner", they are mathematically arguing over who gets to paint that corner of the Bird's Eye View screen.
In `evaluate_bev.py`, instead of blending them, we force them to draw the exact same overlapping physical corner pixel by pixel and mathematically subtract them.

The **Photometric Mean Absolute Error (MAE)** measures how big the color discrepancy is between the two projections. 
If the translation (`tvec`) of the cameras were overlapping incorrectly, the difference map would show harsh edges separating the two textures. Because the metrics read perfectly uniform `(~47.7/255.0)` across all four independent corners with identical MAEs, it mathematically proves perfect alignment symmetry across the entire stitched surface.
