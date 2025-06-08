#!/usr/bin/env python3
"""
Lean setup script for OpenCV CUDA wheel that depends on external CUDA installation
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from setuptools import setup, Extension
from setuptools.dist import Distribution
from wheel.bdist_wheel import bdist_wheel

class BinaryDistribution(Distribution):
    def has_ext_modules(self):
        return True

class CustomBdistWheel(bdist_wheel):
    def finalize_options(self):
        super().finalize_options()
        self.root_is_pure = False

def build_opencv_lean():
    """Build OpenCV libraries without bundling CUDA"""
    
    builddir = "obj-x86_64-linux-gnu"
    
    if not os.path.exists(builddir):
        print("OpenCV build directory not found. Please run debian build first.")
        sys.exit(1)
    
    # Package directory
    pkg_dir = "opencv_cuda"
    lib_dir = f"{pkg_dir}/lib"
    os.makedirs(lib_dir, exist_ok=True)
    
    # Copy OpenCV shared libraries (but not CUDA runtime libs)
    opencv_libs = [
        "libopencv_core.so.4.10.0",
        "libopencv_imgproc.so.4.10.0", 
        "libopencv_imgcodecs.so.4.10.0",
        "libopencv_highgui.so.4.10.0",
        "libopencv_dnn.so.4.10.0",
        "libopencv_video.so.4.10.0",
        "libopencv_videoio.so.4.10.0",
        "libopencv_calib3d.so.4.10.0",
        "libopencv_features2d.so.4.10.0",
        "libopencv_flann.so.4.10.0",
        "libopencv_ml.so.4.10.0",
        "libopencv_objdetect.so.4.10.0",
        "libopencv_photo.so.4.10.0",
        # CUDA-enabled OpenCV modules (but they'll dynamically link to system CUDA)
        "libopencv_cudaarithm.so.4.10.0",
        "libopencv_cudaimgproc.so.4.10.0", 
        "libopencv_cudawarping.so.4.10.0",
        "libopencv_cudafeatures2d.so.4.10.0",
        "libopencv_cudev.so.4.10.0",
    ]
    
    build_lib_dir = Path(builddir) / "lib"
    for lib in opencv_libs:
        src = build_lib_dir / lib
        if src.exists():
            shutil.copy2(src, lib_dir)
            
            # Create version-agnostic symlinks
            base_name = lib.split('.so')[0] + '.so'
            symlink_target = Path(lib_dir) / base_name
            if not symlink_target.exists():
                os.symlink(lib, symlink_target)
    
    # Copy Python bindings
    python_build_dirs = [
        f".pybuild/cpython3_3.12_opencv/build/python_loader",
        f".pybuild/cpython3_3.12_opencv/build/lib",
    ]
    
    for build_dir in python_build_dirs:
        if os.path.exists(build_dir):
            for item in os.listdir(build_dir):
                if item.endswith('.so') or item == 'cv2':
                    src = os.path.join(build_dir, item)
                    dst = os.path.join(pkg_dir, item)
                    if os.path.isdir(src):
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src, dst)

def create_cuda_check_init():
    """Create __init__.py with CUDA detection and path setup"""
    init_content = '''
import os
import sys
import warnings
from pathlib import Path

# Get the directory containing this module
module_dir = Path(__file__).parent

def find_cuda_installation():
    """Find CUDA installation on the system"""
    # First check if we have the pip-installed CUDA runtime
    try:
        import nvidia.cuda_runtime
        # If nvidia-cuda-runtime-cu12 is installed, we should be good
        return "pip-installed"
    except ImportError:
        pass
    
    # Fallback to system CUDA installation
    potential_cuda_paths = [
        "/usr/local/cuda",
        "/usr/local/cuda-12.8", 
        "/usr/local/cuda-12",
        "/opt/cuda",
        "/usr/lib/cuda",
    ]
    
    # Check environment variables
    if "CUDA_HOME" in os.environ:
        potential_cuda_paths.insert(0, os.environ["CUDA_HOME"])
    if "CUDA_ROOT" in os.environ:
        potential_cuda_paths.insert(0, os.environ["CUDA_ROOT"])
    
    for cuda_path in potential_cuda_paths:
        cuda_path = Path(cuda_path)
        if cuda_path.exists():
            # Check for essential CUDA libraries
            lib64_path = cuda_path / "lib64"
            lib_path = cuda_path / "lib"
            
            for lib_dir in [lib64_path, lib_path]:
                if lib_dir.exists():
                    # Look for essential CUDA runtime
                    if (lib_dir / "libcudart.so").exists() or any(lib_dir.glob("libcudart.so.*")):
                        return cuda_path
    
    return None

def setup_library_paths():
    """Setup library paths for OpenCV"""
    # Add OpenCV libraries to path
    opencv_lib_dir = module_dir / "lib"
    if opencv_lib_dir.exists():
        if sys.platform.startswith('linux'):
            current_ld_path = os.environ.get('LD_LIBRARY_PATH', '')
            if str(opencv_lib_dir) not in current_ld_path:
                new_ld_path = f"{opencv_lib_dir}:{current_ld_path}" if current_ld_path else str(opencv_lib_dir)
                os.environ['LD_LIBRARY_PATH'] = new_ld_path
    
    # Check CUDA installation
    cuda_result = find_cuda_installation()
    if cuda_result == "pip-installed":
        print("Using pip-installed CUDA runtime libraries")
    elif cuda_result:
        print(f"Found system CUDA installation at: {cuda_result}")
        
        # Add system CUDA to library path as backup
        cuda_lib_dirs = []
        for lib_subdir in ["lib64", "lib"]:
            cuda_lib_path = cuda_result / lib_subdir
            if cuda_lib_path.exists():
                cuda_lib_dirs.append(str(cuda_lib_path))
        
        if cuda_lib_dirs:
            current_ld_path = os.environ.get('LD_LIBRARY_PATH', '')
            for cuda_lib_dir in cuda_lib_dirs:
                if cuda_lib_dir not in current_ld_path:
                    new_ld_path = f"{cuda_lib_dir}:{current_ld_path}" if current_ld_path else cuda_lib_dir
                    os.environ['LD_LIBRARY_PATH'] = new_ld_path
                    current_ld_path = new_ld_path
    else:
        # This should be rare now since we have pip dependencies
        warnings.warn(
            "No CUDA installation found. The pip-installed CUDA libraries should be sufficient.",
            RuntimeWarning
        )

# Setup paths before importing cv2
setup_library_paths()

# Import cv2
try:
    import cv2
    
    # Check CUDA support
    cuda_devices = cv2.cuda.getCudaEnabledDeviceCount()
    print(f"OpenCV version: {cv2.__version__}")
    print(f"CUDA devices detected: {cuda_devices}")
    
    if cuda_devices == 0:
        warnings.warn(
            "No CUDA devices detected. Ensure NVIDIA GPU and drivers are properly installed.",
            RuntimeWarning
        )
    
    # Re-export cv2 components
    from cv2 import *
    
except ImportError as e:
    print(f"Failed to import cv2: {e}")
    print("This may be due to missing dependencies.")
    raise

except Exception as e:
    print(f"Error initializing OpenCV CUDA: {e}")
    # Still try to import cv2 for CPU-only functionality
    try:
        import cv2
        from cv2 import *
        warnings.warn(f"OpenCV loaded but CUDA initialization failed: {e}", RuntimeWarning)
    except ImportError:
        raise
'''
    
    with open("opencv_cuda/__init__.py", "w") as f:
        f.write(init_content)

def create_requirements_file():
    """Create requirements file documenting dependencies"""
    requirements = '''# OpenCV CUDA Requirements

# Python dependencies (automatically installed with this wheel)
numpy>=1.19.0
nvidia-cuda-runtime-cu12>=12.0
nvidia-cublas-cu12>=12.0
nvidia-cufft-cu12>=11.0
nvidia-curand-cu12>=10.0
nvidia-npp-cu12>=12.0

# System dependencies (must be installed separately):
# - NVIDIA GPU with compute capability 8.0+ (RTX 30/40 series, A100, etc.)
# - NVIDIA Driver 520+ (supports CUDA 12.x)
#
# The CUDA runtime libraries above will be automatically installed via pip.
# No need to install the full CUDA toolkit unless you need development tools.
#
# To verify your GPU and driver:
#   nvidia-smi
#
# To check compute capability:
#   nvidia-ml-py3: pip install nvidia-ml-py3
'''
    
    with open("CUDA_REQUIREMENTS.txt", "w") as f:
        f.write(requirements)

def main():
    # Create package directory
    os.makedirs("opencv_cuda", exist_ok=True)
    
    # Build/copy OpenCV libraries
    build_opencv_lean()
    
    # Create CUDA-aware init file
    create_cuda_check_init()
    
    # Create requirements documentation
    create_requirements_file()
    
    setup(
        name="opencv-cuda",
        version="4.10.0+cuda12.8",
        description="OpenCV with CUDA 12.8 support (requires external CUDA installation)",
        long_description=open("CUDA_REQUIREMENTS.txt").read(),
        long_description_content_type="text/plain",
        author="OpenCV Community", 
        author_email="opencv@opencv.org",
        url="https://opencv.org/",
        packages=["opencv_cuda"],
        package_data={
            "opencv_cuda": [
                "lib/*.so*",
                "*.so",
                "cv2/*.so",
                "cv2/*.py", 
                "cv2/**/*",
            ]
        },
        include_package_data=True,
        distclass=BinaryDistribution,
        cmdclass={'bdist_wheel': CustomBdistWheel},
        install_requires=[
            "numpy>=1.19.0",
            "nvidia-cuda-runtime-cu12>=12.0",
            "nvidia-cublas-cu12>=12.0", 
            "nvidia-cufft-cu12>=11.0",
            "nvidia-curand-cu12>=10.0",
            "nvidia-npp-cu12>=12.0",  # Needed for OpenCV CUDA image processing
        ],
        python_requires=">=3.8",
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Environment :: GPU :: NVIDIA CUDA :: 12",
            "Intended Audience :: Developers",
            "Intended Audience :: Science/Research",
            "License :: OSI Approved :: Apache Software License", 
            "Operating System :: POSIX :: Linux",
            "Programming Language :: Python :: 3",
            "Topic :: Scientific/Engineering :: Image Processing",
            "Topic :: Software Development :: Libraries",
        ],
        zip_safe=False,
    )

if __name__ == "__main__":
    main()
