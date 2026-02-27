# AVM Renderer

This is a Python script that automates the rendering of a four-way surround view (AVM) from a Blender scene using the Blender Python API (`bpy`). 

It iterates through specific predefined cameras in a Blender scene and outputs rendered images for each perspective.

## Prerequisites

You need to run this script within an environment that has Blender installed and supports running Python scripts via `bpy` (such as the background rendering mode in Blender). 

## Structure

- `render_avm.py`: Main rendering script.
- `scenes/avm_v1.blend`: The default Blender scene file used for rendering.
- `data/render_output/`: The default directory where the rendered `.jpg` images will be saved.

## How it works

The `render_avm.py` script executes the following steps:
1. Opens the `avm_v1.blend` scene.
2. Loops through a predefined set of cameras: `"Cam_Front"`, `"Cam_Back"`, `"Cam_Left"`, `"Cam_Right"`.
3. Sets the active camera for the scene.
4. Renders a `.jpg` image for each camera and saves it to the `data/render_output/` folder.

## Running the Script

To run the script inside a headless Blender instance (background mode), you can typically run the following command from the root directory:

```bash
blender -b scenes/avm_v1.blend -P render_avm.py
```

*(Note: The exact command depends on how your Blender environment is packaged or installed.)*

## Outputs

The script will dump four `.jpg` images into `data/render_output/`:
- `Cam_Front.jpg`
- `Cam_Back.jpg`
- `Cam_Left.jpg`
- `Cam_Right.jpg`
