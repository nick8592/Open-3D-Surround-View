import cv2
import numpy as np
import os

# 1. Intrinsic parameters
K = np.array([[561.476, 0, 959.527],
              [0, 449.175, 767.478],
              [0, 0, 1]], dtype=np.float64)
D = np.array([[0.00040877], [-0.00274577], [0.0061865], [-0.00363161]], dtype=np.float64)

def get_pad_3d_points(center_x, center_y, cam_name):
    square_size = 0.25 
    grid_w, grid_h = 7, 5 # 7 corners along width (image X), 5 corners along height (image Y)
    objp = np.zeros((grid_w * grid_h, 3), np.float32)

    if cam_name == "Cam_Front":
        # Image Top -> +Y (further)
        # Image Left -> -X (left)
        start_x = center_x - 3 * square_size
        start_y = center_y + 2 * square_size
        for i in range(grid_h):      # Image down -> Y decreases
            for j in range(grid_w):  # Image right -> X increases
                objp[i * grid_w + j] = [start_x + j * square_size, start_y - i * square_size, 0]

    elif cam_name == "Cam_Back":
        # Image Top -> -Y (further backward)
        # Image Left -> +X (right from car's perspective, but left in backward facing camera)
        start_x = center_x + 3 * square_size
        start_y = center_y - 2 * square_size
        for i in range(grid_h):      # Image down -> Y increases
            for j in range(grid_w):  # Image right -> X decreases
                objp[i * grid_w + j] = [start_x - j * square_size, start_y + i * square_size, 0]

    elif cam_name == "Cam_Right":
        # Image Top -> +X (further right)
        # Image Left -> +Y (forward)
        start_x = center_x + 2 * square_size
        start_y = center_y + 3 * square_size
        for i in range(grid_h):      # Image down -> X decreases
            for j in range(grid_w):  # Image right -> Y decreases
                objp[i * grid_w + j] = [start_x - i * square_size, start_y - j * square_size, 0]

    elif cam_name == "Cam_Left":
        # Image Top -> -X (further left)
        # Image Left -> -Y (backward)
        start_x = center_x - 2 * square_size
        start_y = center_y - 3 * square_size
        for i in range(grid_h):      # Image down -> X increases
            for j in range(grid_w):  # Image right -> Y increases
                objp[i * grid_w + j] = [start_x + i * square_size, start_y + j * square_size, 0]

    return objp, (grid_w, grid_h)

camera_config = {
    "Cam_Front": (0, 3.5),
    "Cam_Back":  (0, -3.5),
    "Cam_Left":  (-2, 0),
    "Cam_Right": (2, 0)
}

def solve_extrinsic_for_camera(cam_name, center):
    img_path = f'data/outputs/surround_view/{cam_name}.png'
    img = cv2.imread(img_path)
    if img is None: return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    obj_pts, pattern_size = get_pad_3d_points(center[0], center[1], cam_name)
    
    ret, corners = cv2.findChessboardCorners(gray, pattern_size, cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE)
    if ret:
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        
        # We must undistort the corners because solvePnP expects pinhole model, but we have a fisheye lens
        undistorted_corners = cv2.fisheye.undistortPoints(
            corners_refined.reshape(-1, 1, 2), K, D, P=K
        )
        
        # Debug Visualization
        vis_img = img.copy()
        cv2.drawChessboardCorners(vis_img, pattern_size, corners_refined, ret)
        cv2.circle(vis_img, tuple(corners_refined[0][0].astype(int)), 15, (0, 0, 255), -1) 
        cv2.imwrite(f'data/outputs/surround_view/debug_{cam_name}.png', vis_img)
        
        # Note: pass D=None, because undistorted_corners are already pinhole-equivalent
        success, rvec, tvec = cv2.solvePnP(obj_pts, undistorted_corners, K, None, flags=cv2.SOLVEPNP_SQPNP)
        
        if success:
            # Calculate actual camera position in world space
            R, _ = cv2.Rodrigues(rvec)
            camera_pos = -np.matrix(R).T * np.matrix(tvec)
            
            # Print stats
            print(f"  {cam_name} Success!")
            print(f"    World Position: X={camera_pos[0,0]:.3f}m, Y={camera_pos[1,0]:.3f}m, Z={camera_pos[2,0]:.3f}m")
            
            return (rvec, tvec)
    return None

results = {}
output_dir = 'data/calibration/params'
os.makedirs(output_dir, exist_ok=True)
for cam, center in camera_config.items():
    print(f"Solving {cam}...")
    ext = solve_extrinsic_for_camera(cam, center)
    if ext:
        rvec, tvec = ext[0], ext[1]
        results[cam] = {"rvec": rvec, "tvec": tvec}
        
        # Save individual .npz
        npz_path = os.path.join(output_dir, f'extrinsic_{cam}.npz')
        np.savez(npz_path, rvec=rvec, tvec=tvec)
        
        # Save individual .xml
        xml_path = os.path.join(output_dir, f'extrinsic_{cam}.xml')
        fs = cv2.FileStorage(xml_path, cv2.FILE_STORAGE_WRITE)
        fs.write("rvec", rvec)
        fs.write("tvec", tvec)
        fs.release()
        
    else:
        print(f"  {cam} Failed.")
        
np.savez(os.path.join(output_dir, 'extrinsics_all.npz'), **results)
print(f"\nAll extrinsics saved successfully in {output_dir}")