#!/bin/bash
set -e

echo "Building OpenCV CUDA Python Wheel"

# Ensure we're in the right directory
if [[ ! -f "debian/rules" ]]; then
    echo "Error: Must run from OpenCV source directory with debian/ folder"
    exit 1
fi

# Ensure the Debian build has completed
if [[ ! -d "obj-x86_64-linux-gnu" ]]; then
    echo "Error: Debian build not found. Please run 'dpkg-buildpackage -b' first"
    exit 1
fi

# Clean any previous wheel builds
rm -rf opencv_cuda/ build/ dist/ *.egg-info/ setup.py

# Install wheel building dependencies
pip3 install --user wheel setuptools build

# Choose which setup.py to use
SETUP_TYPE=${1:-"lean"}

if [[ "$SETUP_TYPE" == "bundled" ]]; then
    echo "Building wheel with bundled CUDA libraries..."
    
    # Use the bundled setup
    cp opencv_cuda_bundled_setup.py setup.py
    
    # Verify CUDA libraries exist
    if [[ ! -d "/usr/local/cuda-12.8/lib64" ]]; then
        echo "Error: CUDA 12.8 libraries not found at /usr/local/cuda-12.8/lib64"
        echo "Please ensure CUDA 12.8 is installed"
        exit 1
    fi
    
    PYTHON_ARGS=""
    
elif [[ "$SETUP_TYPE" == "bundled" ]]; then
    echo "Note: This wheel includes all CUDA runtime libraries (~500MB+)."
    echo "No additional CUDA installation required - only NVIDIA drivers (520+)."
elif [[ "$SETUP_TYPE" == "lean" ]]; then
    echo "Building lean wheel (external CUDA dependency)..."
    
    # Use the lean setup OR the fixed setup without CUDA libs
    if [[ -f "opencv_cuda_lean_setup.py" ]]; then
        cp opencv_cuda_lean_setup.py setup.py
        PYTHON_ARGS=""
    else
        cp opencv_cuda_fixed_setup.py setup.py
        PYTHON_ARGS=""
    fi
    
elif [[ "$SETUP_TYPE" == "original-bundled" ]]; then
    echo "Building with original bundled setup..."
    cp opencv_cuda_setup.py setup.py
    PYTHON_ARGS=""
    
else
    echo "Usage: $0 [bundled|lean|original-bundled]"
    echo "  bundled         - Include CUDA libraries in wheel (larger, self-contained)"
    echo "  lean            - Require external CUDA installation (smaller wheel)"
    echo "  original-bundled - Use original bundled setup"
    exit 1
fi

# Set environment variables for build
export CUDA_HOME=/usr/local/cuda-12.8
export CUDA_ROOT=/usr/local/cuda-12.8
export PATH=/usr/local/cuda-12.8/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda-12.8/lib64:$LD_LIBRARY_PATH

# Build the wheel
echo "Building wheel..."
python3 setup.py bdist_wheel $PYTHON_ARGS

# Show results
echo "Wheel built successfully:"
ls -la dist/

echo ""
echo "To install the wheel:"
echo "  pip install dist/opencv_cuda-*.whl"
echo ""

if [[ "$SETUP_TYPE" == "lean" ]]; then
    echo "Note: This wheel automatically installs CUDA runtime dependencies via pip:"
    echo "  - nvidia-cuda-runtime-cu12"
    echo "  - nvidia-cublas-cu12" 
    echo "  - nvidia-cufft-cu12"
    echo "  - nvidia-curand-cu12"
    echo "  - nvidia-npp-cu12"
    echo "  - numpy"
    echo ""
    echo "Only requires NVIDIA GPU drivers (520+) to be installed separately."
fi

echo ""
echo "To test CUDA functionality:"
echo "  python3 -c \"import opencv_cuda as cv2; print(f'CUDA devices: {cv2.cuda.getCudaEnabledDeviceCount()}')\""

echo ""
echo "Files created:"
echo "  setup.py (copied from $SETUP_TYPE setup)"
echo "  opencv_cuda/ (package directory)"
echo "  dist/opencv_cuda-*.whl (installable wheel)"
