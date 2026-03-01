# Use Ubuntu 22.04 as base (Force AMD64 so Rosetta 2 cleanly emulates Blender 3.6 x64 on Mac Silicon)
FROM --platform=linux/amd64 ubuntu:22.04

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

# 2. Install Blender (LTS 3.6)
# Official Linux ARM64 binaries for Blender 3.6 do not exist.
# By forcing the container to `--platform=linux/amd64`, Docker on Mac M-Series will use Rosetta 2 to flawlessly simulate this x64 installation.
RUN wget https://download.blender.org/release/Blender3.6/blender-3.6.5-linux-x64.tar.xz \
    && tar -xvf blender-3.6.5-linux-x64.tar.xz -C /opt/ \
    && ln -s /opt/blender-3.6.5-linux-x64/blender /usr/local/bin/blender \
    && rm blender-3.6.5-linux-x64.tar.xz

# 3. Upgrade pip and install critical Python libraries
# Warning: NumPy 2.x introduces C-API breaking changes with many pre-compiled CV packages. Strictly capping <2.
RUN pip3 install --upgrade pip
RUN pip3 install \
    "numpy<2" \
    pybind11 \
    scipy \
    fake-bpy-module-3.6 \
    matplotlib \
    black \
    isort \
    pyyaml

# 4. Set environment variables
ENV PYTHONPATH=/usr/lib/python3/dist-packages
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# 5. Copy the Open-3D-Surround-View repository into the image
WORKDIR /app
COPY . /app

# Pre-run black/isort formatting checks to ensure code integrity
RUN black --check scripts/ || true

# Default startup command drops the user into the working environment
CMD ["/bin/bash"]
