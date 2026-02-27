# 使用 Ubuntu 22.04 作為基礎，自動適應 Mac M 晶片的 ARM64 架構
FROM ubuntu:22.04

# 避免安裝過程中的交互詢問
ENV DEBIAN_FRONTEND=noninteractive

# 1. 安裝系統核心工具與渲染依賴
# 這裡包含 OpenCV 視窗顯示與 Blender 執行必備的 OpenGL、X11 函式庫
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

# 2. 安裝 Blender (以 3.6 LTS 為例)
# 注意：若需 4.2 版，請替換下方網址。
# 在 Mac M 晶片 Docker 中，建議下載 Linux x64 版本，Docker 會透過 Rosetta 2 模擬執行
RUN wget https://download.blender.org/release/Blender3.6/blender-3.6.5-linux-x64.tar.xz \
    && tar -xvf blender-3.6.5-linux-x64.tar.xz -C /opt/ \
    && ln -s /opt/blender-3.6.5-linux-x64/blender /usr/local/bin/blender

# 3. 升級 pip 並安裝 Python 關鍵庫
RUN pip3 install --upgrade pip
RUN pip3 install \
    numpy \
    pybind11 \
    scipy \
    fake-bpy-module-3.6 \
    matplotlib

# 4. 設定環境變數
# 確保 Python 能找到 OpenCV
ENV PYTHONPATH=/usr/lib/python3/dist-packages:$PYTHONPATH
# 解決部分 OpenCV 初始化時的編碼問題
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

WORKDIR /workspace