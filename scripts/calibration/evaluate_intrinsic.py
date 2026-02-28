import os

import cv2
import numpy as np


def verify():
    # Determine project root (base_dir)
    if os.path.exists("/workspace/data/calibration"):
        base_dir = "/workspace"
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.abspath(os.path.join(script_dir, "../../"))

    img_path = os.path.join(
        base_dir, "data/calibration/intrinsic/images/intrinsic_calib_0.png"
    )
    if not os.path.exists(img_path):
        print(f"Error: Target image not found at {img_path}")
        return

    img = cv2.imread(img_path)
    h, w = img.shape[:2]

    # 1. Load calibrated intrinsic parameters
    params_path = os.path.join(
        base_dir, "data/calibration/intrinsic/params/intrinsic_params.npz"
    )
    if not os.path.exists(params_path):
        print(f"Error: Calibration parameters not found at {params_path}")
        print("Please run calibrate_intrinsics.py first.")
        return

    with np.load(params_path) as data:
        K = data["K"]
        D = data["D"]

    print(f"Loaded parameters from {params_path}")

    # 2. Manually construct a new K, forcing a 1:1 aspect ratio and adjusting scale
    # We take the fx from calibrated K as the baseline and multiply by a scale factor
    scale = 0.5  # Smaller value = wider field of view; larger value = zoomed in
    new_f = K[0, 0] * scale

    new_K = np.array(
        [
            [new_f, 0, w / 2],  # Center cx set to half of image width
            [0, new_f, h / 2],  # Center cy set to half of image height
            [0, 0, 1],
        ],
        dtype=np.float64,
    )

    # 3. Perform undistortion
    map1, map2 = cv2.fisheye.initUndistortRectifyMap(
        K, D, np.eye(3), new_K, (w, h), cv2.CV_16SC2
    )
    undistorted_img = cv2.remap(
        img, map1, map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT
    )

    output_path = os.path.join(
        base_dir, "data/calibration/intrinsic/debug/test_undistort.png"
    )
    cv2.imwrite(output_path, undistorted_img)
    print(f"Undistorted image saved to: {output_path}")

    # 4. Evaluate Plumb-Line Curvature Variance (Straightness Metric)
    # Finding corners on heavily scaled/bordered images is very flaky.
    # We find the corners in the original image, mathematically undistort the points,
    # and then calculate their straightness variance.
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, corners = cv2.findChessboardCorners(
        gray,
        (7, 7),
        cv2.CALIB_CB_ADAPTIVE_THRESH
        + cv2.CALIB_CB_FAST_CHECK
        + cv2.CALIB_CB_NORMALIZE_IMAGE,
    )

    if ret:
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)

        # Undistort the specific points mathematically
        # Use the mapped new_K to project them into the same scaling as our visual
        undistorted_pts = cv2.fisheye.undistortPoints(corners_refined, K, D, P=new_K)
        corners_refined = undistorted_pts.reshape(7, 7, 2)

        errors = []

        # Calculate straightness deviation for rows
        for i in range(7):
            row = corners_refined[i, :, :]
            [vx, vy, x, y] = cv2.fitLine(row, cv2.DIST_L2, 0, 0.01, 0.01)
            for j in range(7):
                pt = row[j]
                # Perpendicular distance from point to the fitted line
                dist = abs((pt[0] - x[0]) * vy[0] - (pt[1] - y[0]) * vx[0]) / np.sqrt(
                    vx[0] ** 2 + vy[0] ** 2
                )
                errors.append(dist)

        # Calculate straightness deviation for columns
        for j in range(7):
            col = corners_refined[:, j, :]
            [vx, vy, x, y] = cv2.fitLine(col, cv2.DIST_L2, 0, 0.01, 0.01)
            for i in range(7):
                pt = col[i]
                dist = abs((pt[0] - x[0]) * vy[0] - (pt[1] - y[0]) * vx[0]) / np.sqrt(
                    vx[0] ** 2 + vy[0] ** 2
                )
                errors.append(dist)

        mean_curvature_error = np.mean(errors)
        max_curvature_error = np.max(errors)
        variance_curvature = np.var(errors)

        print("\nPlumb-Line Curvature Metrics (Straightness):")
        print("-" * 50)
        print(f"Mean Error:     {mean_curvature_error:.4f} pixels")
        print(f"Max Error:      {max_curvature_error:.4f} pixels")
        print(f"Error Variance: {variance_curvature:.6f} pixels^2")
        print("-" * 50)

        # Overlay straight lines for visual debugging using the undistorted points
        vis_img = undistorted_img.copy()
        for i in range(7):
            cv2.line(
                vis_img,
                tuple(corners_refined[i, 0].astype(int)),
                tuple(corners_refined[i, 6].astype(int)),
                (0, 255, 0),
                1,
            )
            # Draw points
            for j in range(7):
                cv2.circle(
                    vis_img,
                    tuple(corners_refined[i, j].astype(int)),
                    3,
                    (0, 0, 255),
                    -1,
                )
        for j in range(7):
            cv2.line(
                vis_img,
                tuple(corners_refined[0, j].astype(int)),
                tuple(corners_refined[6, j].astype(int)),
                (0, 255, 0),
                1,
            )

        plumbline_path = os.path.join(
            base_dir, "data/calibration/intrinsic/debug/test_plumbline.png"
        )
        cv2.imwrite(plumbline_path, vis_img)
        print(f"Plumb-line debug image saved to: {plumbline_path}")
    else:
        print(
            "Could not find checkerboard corners in original image for plumb-line evaluation."
        )


if __name__ == "__main__":
    verify()
