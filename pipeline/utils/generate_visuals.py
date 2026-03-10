import cv2
import numpy as np
import os
from PIL import Image

base_dir = "."
docs_img_dir = "docs/images"
os.makedirs(docs_img_dir, exist_ok=True)

# 1. Load images
front = cv2.imread("data/sample/front.jpg")
back = cv2.imread("data/sample/back.jpg")
left = cv2.imread("data/sample/left.jpg")
right = cv2.imread("data/sample/right.jpg")

bev = cv2.imread("demo/demo_bev.png")
bowl = cv2.imread("demo/demo_bowl.png")

print("Generating Comparison Image...")
def resize_pad(img, w, h):
    return cv2.resize(img, (w, h))

def draw_text_bg(img, text, pos, font_scale, thickness):
    font = cv2.FONT_HERSHEY_SIMPLEX
    (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    x, y = pos
    cv2.rectangle(img, (x - 5, y - text_h - 5), (x + text_w + 5, y + baseline + 5), (0, 0, 0), -1)
    cv2.putText(img, text, (x, y), font, font_scale, (255, 255, 255), thickness)

w, h = 320, 240
fc = resize_pad(front, w, h)
bc = resize_pad(back, w, h)
lc = resize_pad(left, w, h)
rc = resize_pad(right, w, h)

# Create a 3x3 layout for cameras
empty = np.zeros((h, w, 3), dtype=np.uint8)
row1 = np.hstack([empty, fc, empty])
row2 = np.hstack([lc, empty, rc])
row3 = np.hstack([empty, bc, empty])
cams_grid = np.vstack([row1, row2, row3]) # 720 x 960

draw_text_bg(cams_grid, "Fisheye Inputs", (50, 50), 0.9, 2)

# Add separator and output column (BEV and BOWL 360x360 each)
bev_res = cv2.resize(bev, (360, 360))
bowl_res = cv2.resize(bowl, (360, 360))

# Add a gray border around them
cv2.rectangle(bev_res, (0,0), (359,359), (100,100,100), 2)
cv2.rectangle(bowl_res, (0,0), (359,359), (100,100,100), 2)

# Write labels
draw_text_bg(bev_res, "2D BEV", (20, 40), 0.8, 2)
draw_text_bg(bowl_res, "3D Bowl", (20, 40), 0.8, 2)

outputs_col = np.vstack([bev_res, bowl_res]) # 720 x 360

comparison = np.hstack([cams_grid, outputs_col]) # 720 x 1320
cv2.imwrite(os.path.join(docs_img_dir, "comparison.png"), comparison)

print("Generating Animation GIF...")
frames = []

def np_to_pil(cv_img):
    return Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))

# 640x640 GIF Background
gif_size = 640
cam_bg = np.zeros((gif_size, gif_size, 3), dtype=np.uint8)

# Center 4 cameras in a "+" layout
cw, ch = 240, 180
cam_bg[30:30+ch, gif_size//2-cw//2:gif_size//2+cw//2] = cv2.resize(front, (cw, ch))
cam_bg[gif_size-30-ch:gif_size-30, gif_size//2-cw//2:gif_size//2+cw//2] = cv2.resize(back, (cw, ch))
cam_bg[gif_size//2-ch//2:gif_size//2+ch//2, 30:30+cw] = cv2.resize(left, (cw, ch))
cam_bg[gif_size//2-ch//2:gif_size//2+ch//2, gif_size-30-cw:gif_size-30] = cv2.resize(right, (cw, ch))
draw_text_bg(cam_bg, "Fisheye", (30, 40), 0.9, 2)

# Draw lines indicating car pointing
cv2.rectangle(cam_bg, (gif_size//2-20, gif_size//2-40), (gif_size//2+20, gif_size//2+40), (200, 200, 200), -1)

bev_bg = cv2.resize(bev, (gif_size, gif_size))
draw_text_bg(bev_bg, "2D BEV", (30, 40), 0.9, 2)

bowl_bg = cv2.resize(bowl, (gif_size, gif_size))
draw_text_bg(bowl_bg, "3D Bowl", (30, 40), 0.9, 2)

# Simple crossfade sequence
imgs = [cam_bg, bev_bg, bowl_bg]
for i in range(len(imgs)):
    curr = imgs[i]
    nxt = imgs[(i+1)%len(imgs)]
    
    # Hold the frame
    for _ in range(12):
        frames.append(np_to_pil(curr))
        
    # Fade
    for alpha_int in range(1, 6):
        alpha = alpha_int / 6.0
        blended = cv2.addWeighted(curr, 1 - alpha, nxt, alpha, 0)
        frames.append(np_to_pil(blended))

frames[0].save(os.path.join(docs_img_dir, "animation.gif"), format='GIF',
               append_images=frames[1:], save_all=True, duration=150, loop=0)

print("Visuals generated successfully in docs/images/ !")
