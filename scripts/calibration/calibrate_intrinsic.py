"""
Module: calibrate_intrinsic.py

This module provides functionality related to calibrate intrinsic.
"""

import glob
import os

import cv2
import numpy as np

# Configuration
CHECKERBOARD = (7, 7)
SUBPIX_CRITERIA = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.1)


def calibrate():
    # Prepare 3D object points in real world space: (0,0,0), (1,0,0), (2,0,0) ...
    objp = np.zeros((1, CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
    objp[0, :, :2] = np.mgrid[0 : CHECKERBOARD[0], 0 : CHECKERBOARD[1]].T.reshape(-1, 2)

    objpoints = []  # 3D points in real world space
    imgpoints = []  # 2D points in image plane

    # Determine project root (base_dir)
    if os.path.exists("/workspace/data/calibration"):
        base_dir = "/workspace"
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.abspath(os.path.join(script_dir, "../../"))

    # Define paths based on project root
    input_pattern = os.path.join(base_dir, "data/calibration/intrinsic/images/*.png")
    debug_dir = os.path.join(base_dir, "data/calibration/intrinsic/debug")
    params_dir = os.path.join(base_dir, "data/calibration/intrinsic/params")
    os.makedirs(debug_dir, exist_ok=True)
    os.makedirs(params_dir, exist_ok=True)

    images = glob.glob(input_pattern)
    if not images:
        print(f"Error: No images found matching {input_pattern}")
        return

    print(f"Processing {len(images)} images...")

    gray_shape = None
    for fname in images:
        img = cv2.imread(fname)
        if img is None:
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray_shape = gray.shape[::-1]

        # Find the chess board corners
        ret, corners = cv2.findChessboardCorners(
            gray,
            CHECKERBOARD,
            cv2.CALIB_CB_ADAPTIVE_THRESH
            + cv2.CALIB_CB_FAST_CHECK
            + cv2.CALIB_CB_NORMALIZE_IMAGE,
        )

        if ret:
            objpoints.append(objp)
            # Refine corner coordinates
            cv2.cornerSubPix(gray, corners, (3, 3), (-1, -1), SUBPIX_CRITERIA)
            imgpoints.append(corners)

            # Save detection result for verification
            cv2.drawChessboardCorners(img, CHECKERBOARD, corners, ret)
            output_path = os.path.join(debug_dir, f"debug_{os.path.basename(fname)}")
            cv2.imwrite(output_path, img)
            print(f"  [OK]  {os.path.basename(fname)}")
        else:
            print(f"  [Skip] {os.path.basename(fname)} (Corners not found)")

    # 3. Perform Fisheye Calibration
    if len(objpoints) > 0:
        n_ok = len(objpoints)
        k_matrix = np.zeros((3, 3))
        d_coeffs = np.zeros((4, 1))
        rvecs = [np.zeros((1, 1, 3), dtype=np.float32) for _ in range(n_ok)]
        tvecs = [np.zeros((1, 1, 3), dtype=np.float32) for _ in range(n_ok)]

        # Calibration flags for Equidistant model
        # Note: cv2.fisheye.CALIB_FIX_ASPECT_RATIO does not exist in some versions,
        # Using standard flags.
        rms, _, _, _, _ = cv2.fisheye.calibrate(
            objpoints,
            imgpoints,
            gray_shape,
            k_matrix,
            d_coeffs,
            rvecs,
            tvecs,
            cv2.fisheye.CALIB_RECOMPUTE_EXTRINSIC + cv2.fisheye.CALIB_FIX_SKEW,
            (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-6),
        )

        print("-" * 40)
        print(f"Calibration successful with {n_ok} image(s)")
        print(f"RMS Error: {rms:.6f}")
        print("\nIntrinsic Matrix K:")
        print(np.array2string(k_matrix, precision=4, suppress_small=True))
        print("\nDistortion Coefficients D:")
        print(np.array2string(d_coeffs, precision=6, suppress_small=True))
        print("-" * 40)

        # 4. Save results
        # Save as .npz for Python/NumPy use
        npz_path = os.path.join(params_dir, "intrinsic_params.npz")
        np.savez(npz_path, K=k_matrix, D=d_coeffs)
        print(f"Saved NumPy format to: {npz_path}")

        # Save as .xml for OpenCV/C++ compatibility
        xml_path = os.path.join(params_dir, "intrinsic_params.xml")
        fs = cv2.FileStorage(xml_path, cv2.FILE_STORAGE_WRITE)
        fs.write("K", k_matrix)
        fs.write("D", d_coeffs)
        fs.write("RMS", rms)
        fs.release()
        print(f"Saved XML format to: {xml_path}")
    else:
        print("Error: Could not find any checkerboard corners in provided images.")


if __name__ == "__main__":
    calibrate()
