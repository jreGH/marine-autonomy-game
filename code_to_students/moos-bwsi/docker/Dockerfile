# bwsi-moos-base — MOOS-IvP + BWSI behaviors
#
# Build from the root of the moos-bwsi directory:
#   docker build -f docker/Dockerfile -t bwsi-moos-base:latest .
#
# The image bakes in both MOOS-IvP (from source) and the compiled BWSI
# behaviors so that containers start instantly with no build step.

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# ---- System dependencies ----
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    g++ \
    git \
    wget \
    libfltk1.3-dev \
    libtiff-dev \
    libxinerama-dev \
    libxft-dev \
    libxrender-dev \
    libpng-dev \
    libgl1-mesa-dev \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# ---- Build MOOS-IvP from a pinned release ----
WORKDIR /root
RUN git clone --depth 1 --branch ivp-23.8 \
    https://github.com/moos-ivp/moos-ivp.git moos-ivp \
    && cd moos-ivp \
    && ./build.sh \
    && rm -rf moos-ivp/build   # remove build artifacts to shrink layer

ENV PATH="/root/moos-ivp/bin:/root/moos-bwsi/behaviors/bin:${PATH}"
ENV IVP_BEHAVIOR_DIRS="/root/moos-bwsi/behaviors/bin"

# ---- Copy and build the BWSI behaviors ----
WORKDIR /root/moos-bwsi
COPY . .
RUN ./build_all.sh

# ---- Python utilities ----
RUN pip3 install tomli pymoos

# ---- Working directory for generated mission files ----
WORKDIR /mission

# Default command: show usage hint
CMD ["bash", "-c", "echo 'Usage: pAntler <name>.moos  (mount mission files at /mission)'"]
