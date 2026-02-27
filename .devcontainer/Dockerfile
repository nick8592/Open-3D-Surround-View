# Use Ubuntu 22.04 as base
FROM ubuntu:22.04

# Avoid interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# 1. Install core system tools and rendering dependencies
# Includes libraries for OpenCV window display and Blender OpenGL/X11 requirements
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    python3-opencv \
    libgl1-mesa-dev \
    libglu1-mesa \
    libxi6 \
    libxrender1 \
    libxkbcommon0 \
    libsm6 \
    libxext6 \
    libdbus-1-3 \
    wget \
    xz-utils \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Blender (LTS 3.6 example)
# Note: To use Blender 4.2+, replace the download URL accordingly.
# On Mac M-series Docker, Linux x64 version is often used via Rosetta 2 emulation
RUN wget https://download.blender.org/release/Blender3.6/blender-3.6.5-linux-x64.tar.xz \
    && tar -xvf blender-3.6.5-linux-x64.tar.xz -C /opt/ \
    && ln -s /opt/blender-3.6.5-linux-x64/blender /usr/local/bin/blender

# 3. Upgrade pip and install critical Python libraries
RUN pip3 install --upgrade pip
RUN pip3 install \
    "numpy<2" \
    pybind11 \
    scipy \
    fake-bpy-module-3.6 \
    matplotlib

# 4. Set environment variables
# Ensure Python can find system OpenCV
ENV PYTHONPATH=/usr/lib/python3/dist-packages:$PYTHONPATH
# Solve encoding issues for some OpenCV initializations
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

WORKDIR /workspace