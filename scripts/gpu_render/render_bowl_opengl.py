import cv2
import numpy as np
import glfw
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import glm
import os

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Open-3D-Surround-View: GPU Renderer Preview"

def load_text(filename):
    with open(filename, 'r') as f:
        return f.read()

def compile_custom_shader(vert_path, frag_path):
    vertex_src = load_text(vert_path)
    fragment_src = load_text(frag_path)

    shader_program = compileProgram(
        compileShader(vertex_src, GL_VERTEX_SHADER),
        compileShader(fragment_src, GL_FRAGMENT_SHADER)
    )
    return shader_program

def create_texture_from_data(img_data, is_float=False):
    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    
    # Texture wrapping & filtering
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    
    height, width = img_data.shape[:2]
    ch = img_data.shape[2] if len(img_data.shape) == 3 else 1
    
    if ch == 4:
        input_format = GL_RGBA
        internal_format = GL_RGBA32F if is_float else GL_RGBA
    elif ch == 3:
        input_format = GL_RGB
        internal_format = GL_RGB32F if is_float else GL_RGB
    elif ch == 2:
        input_format = GL_RG
        internal_format = GL_RG32F if is_float else GL_RG
    else:
        input_format = GL_RED
        internal_format = GL_R32F if is_float else GL_RED
    
    data_type = GL_FLOAT if is_float else GL_UNSIGNED_BYTE
    
    # Ensure memory is contiguous C-style array before passing to C++ level OpenGL
    img_data = np.ascontiguousarray(img_data)
    
    glTexImage2D(GL_TEXTURE_2D, 0, internal_format, width, height, 0, input_format, data_type, img_data)
    
    glBindTexture(GL_TEXTURE_2D, 0)
    return tex_id

def load_binary_texture(filepath, shape, is_float=True):
    dtype = np.float32 if is_float else np.uint8
    data = np.fromfile(filepath, dtype=dtype)
    data = data.reshape(shape)
    
    # We must flip the data vertically because OpenCV/NumPy origin (top-left) 
    # conflicts with OpenGL origin (bottom-left)
    data = np.flipud(data)
    
    return create_texture_from_data(data, is_float=is_float)

def load_camera_texture(filepath):
    img = cv2.imread(filepath)
    if img is None:
        print(f"Warning: Could not load {filepath}")
        return create_texture_from_data(np.full((512, 512, 3), (255, 0, 255), dtype=np.uint8))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Flip to align OpenCV image coordinates with OpenGL Texture coords
    # Wait, we'll NOT flip the raw images because the map_y from the mathematical LUT natively targets Top-Left!
    # Let's keep it as is.
    return create_texture_from_data(img, is_float=False)

def main():
    if not glfw.init():
        print("Failed to initialize GLFW!")
        return

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.VISIBLE, glfw.FALSE) # Hide window for headless

    window = glfw.create_window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, None, None)
    if not window:
        print("Failed to create GLFW window!")
        glfw.terminate()
        return

    glfw.make_context_current(window)
    glfw.swap_interval(1)

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    proj_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    
    shader_program = compile_custom_shader(
        os.path.join(script_dir, "shaders", "svm_bowl.vert"),
        os.path.join(script_dir, "shaders", "svm_bowl.frag")
    )

    # Basic flat Quad, showing complete 0.0 to 1.0 UV range
    vertices = np.array([
         1.0,  1.0, 0.0,   1.0, 1.0,
         1.0, -1.0, 0.0,   1.0, 0.0,
        -1.0, -1.0, 0.0,   0.0, 0.0,
        -1.0,  1.0, 0.0,   0.0, 1.0
    ], dtype=np.float32)

    indices = np.array([0, 1, 3, 1, 2, 3], dtype=np.uint32)

    vao = glGenVertexArrays(1)
    glBindVertexArray(vao)

    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

    ebo = glGenBuffers(1)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * vertices.itemsize, ctypes.c_void_p(0))
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * vertices.itemsize, ctypes.c_void_p(3 * vertices.itemsize))
    glEnableVertexAttribArray(1)
    glBindVertexArray(0)

    print("Loading GPU textures...")
    gpu_assets_dir = os.path.join(proj_root, "data", "gpu_assets")
    sample_dir = os.path.join(proj_root, "data", "sample")

    lut_shape = (1000, 1000, 2)
    tex_lut_front = load_binary_texture(os.path.join(gpu_assets_dir, "lut_Front.bin"), lut_shape, True)
    tex_lut_back  = load_binary_texture(os.path.join(gpu_assets_dir, "lut_Back.bin"), lut_shape, True)
    tex_lut_left  = load_binary_texture(os.path.join(gpu_assets_dir, "lut_Left.bin"), lut_shape, True)
    tex_lut_right = load_binary_texture(os.path.join(gpu_assets_dir, "lut_Right.bin"), lut_shape, True)

    tex_blend_mask = load_binary_texture(os.path.join(gpu_assets_dir, "blend_mask.bin"), (1000, 1000, 4), True)

    tex_cam_front = load_camera_texture(os.path.join(sample_dir, "front.jpg"))
    tex_cam_back  = load_camera_texture(os.path.join(sample_dir, "back.jpg"))
    tex_cam_left  = load_camera_texture(os.path.join(sample_dir, "left.jpg"))
    tex_cam_right = load_camera_texture(os.path.join(sample_dir, "right.jpg"))

    glUseProgram(shader_program)
    
    # 9 Distinct Texture Units!
    glUniform1i(glGetUniformLocation(shader_program, "textureFront"), 0)
    glUniform1i(glGetUniformLocation(shader_program, "textureBack"), 1)
    glUniform1i(glGetUniformLocation(shader_program, "textureLeft"), 2)
    glUniform1i(glGetUniformLocation(shader_program, "textureRight"), 3)
    glUniform1i(glGetUniformLocation(shader_program, "lutFront"), 4)
    glUniform1i(glGetUniformLocation(shader_program, "lutBack"), 5)
    glUniform1i(glGetUniformLocation(shader_program, "lutLeft"), 6)
    glUniform1i(glGetUniformLocation(shader_program, "lutRight"), 7)
    glUniform1i(glGetUniformLocation(shader_program, "blendMask"), 8)

    model_loc = glGetUniformLocation(shader_program, "model")
    view_loc = glGetUniformLocation(shader_program, "view")
    proj_loc = glGetUniformLocation(shader_program, "projection")

    print("Rendering single frame to buffer...")
    glClearColor(0.2, 0.2, 0.2, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    glUseProgram(shader_program)

    # Basic flat top-down view to see the whole quad
    model = glm.translate(glm.mat4(1.0), glm.vec3(0.0, 0.0, 0.0))
    # Move camera back enough to see the -1 to 1 quad 
    view = glm.translate(glm.mat4(1.0), glm.vec3(0.0, 0.0, -2.5)) 
    projection = glm.perspective(glm.radians(45.0), WINDOW_WIDTH / WINDOW_HEIGHT, 0.1, 100.0)

    glUniformMatrix4fv(model_loc, 1, GL_FALSE, glm.value_ptr(model))
    glUniformMatrix4fv(view_loc, 1, GL_FALSE, glm.value_ptr(view))
    glUniformMatrix4fv(proj_loc, 1, GL_FALSE, glm.value_ptr(projection))

    # Bind 9 textures to their slots
    textures = [
        (GL_TEXTURE0, tex_cam_front),    (GL_TEXTURE1, tex_cam_back),
        (GL_TEXTURE2, tex_cam_left),     (GL_TEXTURE3, tex_cam_right),
        (GL_TEXTURE4, tex_lut_front),    (GL_TEXTURE5, tex_lut_back),
        (GL_TEXTURE6, tex_lut_left),     (GL_TEXTURE7, tex_lut_right),
        (GL_TEXTURE8, tex_blend_mask)
    ]
    for tex_unit, tex_id in textures:
        glActiveTexture(tex_unit)
        glBindTexture(GL_TEXTURE_2D, tex_id)
    
    glBindVertexArray(vao)
    glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)

    glfw.swap_buffers(window)
    glfw.poll_events()

    # Read the pixels straight from the OpenGL Framebuffer
    glPixelStorei(GL_PACK_ALIGNMENT, 1)
    data = glReadPixels(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, GL_RGB, GL_UNSIGNED_BYTE)
    image = np.frombuffer(data, dtype=np.uint8).reshape(WINDOW_HEIGHT, WINDOW_WIDTH, 3)
    
    # Flip vertically (OpenGL bottom-left to OpenCV top-left) and swap RGB to BGR
    image = np.flipud(image)
    image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    out_path = os.path.join(proj_root, "gpu_preview.png")
    cv2.imwrite(out_path, image_bgr)
    print(f"Successfully rendered and saved to: {out_path}")

    glfw.terminate()

if __name__ == "__main__":
    main()
