#!/usr/bin/env python3
"""
Bundled setup script for OpenCV CUDA wheel that includes CUDA libraries
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

def copy_cuda_libraries():
    """Copy required CUDA libraries into the wheel"""
    cuda_root = "/usr/local/cuda-12.8"
    target_dir = "opencv_cuda/data/cuda_libs"
    
    os.makedirs(target_dir, exist_ok=True)
    
    # Essential CUDA runtime libraries for OpenCV
    cuda_libs = [
        "libcudart.so.12",
        "libcublas.so.12", 
        "libcublasLt.so.12",
        "libcufft.so.11",
        "libcurand.so.10",
        "libnppc.so.12",
        "libnpps.so.12", 
        "libnppi.so.12",
        "libnppial.so.12",
        "libnppicc.so.12",
        "libnppicom.so.12",
        "libnppidei.so.12",
        "libnppif.so.12",
        "libnppig.so.12",
        "libnppim.so.12",
        "libnppist.so.12",
        "libnppisu.so.12",
        "libnppitc.so.12",
        "libnvjitlink.so.12",
    ]
    
    # Also include cuDNN if available
    cudnn_libs = [
        "libcudnn.so.9",
        "libcudnn_ops.so.9",
        "libcudnn_cnn.so.9",
        "libcudnn_adv.so.9",
    ]
    
    all_libs = cuda_libs + cudnn_libs
    
    for lib in all_libs:
        src_path = Path(cuda_root) / "lib64" / lib
        if src_path.exists():
            shutil.copy2(src_path, target_dir)
            print(f"Copied {lib}")
        else:
            print(f"Warning: {lib} not found at {src_path}")
            
    # Also copy some important symlinks
    lib64_path = Path(cuda_root) / "lib64"
    if lib64_path.exists():
        for lib_file in lib64_path.glob("*.so"):
            if lib_file.is_symlink():
                target_file = target_dir / lib_file.name
                if not target_file.exists():
                    try:
                        # Copy the symlink target
                        real_file = lib_file.resolve()
                        if real_file.exists() and real_file.name in [lib.split('.so')[0] + lib.split('.so')[1] for lib in all_libs]:
                            shutil.copy2(real_file, target_file)
                            print(f"Copied symlink target: {lib_file.name}")
                    except Exception as e:
                        print(f"Warning: Could not copy symlink {lib_file.name}: {e}")

def build_opencv_bundled():
    """Build OpenCV libraries for bundled distribution"""
    
    builddir = "obj-x86_64-linux-gnu"
    
    if not os.path.exists(builddir):
        print("OpenCV build directory not found. Please run debian build first.")
        sys.exit(1)
    
    # Create package structure
    pkg_dir = "opencv_cuda"
    lib_dir = f"{pkg_dir}/data/lib"
    os.makedirs(lib_dir, exist_ok=True)
    os.makedirs(f"{pkg_dir}/data", exist_ok=True)
    
    # Copy OpenCV shared libraries
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
        "libopencv_stitching.so.4.10.0",
        "libopencv_superres.so.4.10.0",
        "libopencv_videostab.so.4.10.0",
        "libopencv_shape.so.4.10.0",
        # CUDA-specific libraries
        "libopencv_cudaarithm.so.4.10.0",
        "libopencv_cudaimgproc.so.4.10.0", 
        "libopencv_cudawarping.so.4.10.0",
        "libopencv_cudafeatures2d.so.4.10.0",
        "libopencv_cudafilters.so.4.10.0",
        "libopencv_cudaobjdetect.so.4.10.0",
        "libopencv_cudaoptflow.so.4.10.0",
        "libopencv_cudastereo.so.4.10.0",
        "libopencv_cudabgsegm.so.4.10.0",
        "libopencv_cudalegacy.so.4.10.0",
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
                print(f"Created symlink: {base_name} -> {lib}")
    
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

def create_bundled_init():
    """Create __init__.py for bundled version"""
    init_content = '''
import os
import sys
import warnings
from pathlib import Path

# Get the directory containing this module
module_dir = Path(__file__).parent

def setup_bundled_libraries():
    """Setup library paths for bundled OpenCV and CUDA"""
    
    # Add bundled CUDA libraries to path
    cuda_lib_dir = module_dir / "data" / "cuda_libs"
    opencv_lib_dir = module_dir / "data" / "lib"
    
    if sys.platform.startswith('linux'):
        current_ld_path = os.environ.get('LD_LIBRARY_PATH', '')
        lib_paths_to_add = []
        
        # Add CUDA libraries first (higher priority)
        if cuda_lib_dir.exists():
            lib_paths_to_add.append(str(cuda_lib_dir))
            
        # Add OpenCV libraries
        if opencv_lib_dir.exists():
            lib_paths_to_add.append(str(opencv_lib_dir))
        
        # Update LD_LIBRARY_PATH
        for lib_path in lib_paths_to_add:
            if lib_path not in current_ld_path:
                new_ld_path = f"{lib_path}:{current_ld_path}" if current_ld_path else lib_path
                os.environ['LD_LIBRARY_PATH'] = new_ld_path
                current_ld_path = new_ld_path
        
        print(f"Using bundled CUDA libraries from: {cuda_lib_dir}")
        print(f"Using bundled OpenCV libraries from: {opencv_lib_dir}")
    
    elif sys.platform == "win32":
        # On Windows, add to PATH
        cuda_lib_dir_win = cuda_lib_dir
        opencv_lib_dir_win = opencv_lib_dir
        
        current_path = os.environ.get('PATH', '')
        
        if cuda_lib_dir_win.exists():
            os.environ['PATH'] = f"{cuda_lib_dir_win};{current_path}"
            
        if opencv_lib_dir_win.exists():
            os.environ['PATH'] = f"{opencv_lib_dir_win};{os.environ['PATH']}"

def verify_cuda_libraries():
    """Verify that bundled CUDA libraries are present"""
    cuda_lib_dir = module_dir / "data" / "cuda_libs"
    
    if not cuda_lib_dir.exists():
        warnings.warn("Bundled CUDA libraries directory not found", RuntimeWarning)
        return False
        
    essential_libs = ["libcudart.so.12", "libcublas.so.12", "libcufft.so.11"]
    missing_libs = []
    
    for lib in essential_libs:
        if not (cuda_lib_dir / lib).exists():
            missing_libs.append(lib)
    
    if missing_libs:
        warnings.warn(f"Missing essential CUDA libraries: {missing_libs}", RuntimeWarning)
        return False
        
    return True

# Setup bundled libraries before importing cv2
setup_bundled_libraries()

# Verify CUDA libraries
cuda_ok = verify_cuda_libraries()

# Import cv2
try:
    import cv2
    
    # Check CUDA support
    cuda_devices = cv2.cuda.getCudaEnabledDeviceCount()
    print(f"OpenCV version: {cv2.__version__}")
    print(f"CUDA devices detected: {cuda_devices}")
    
    if cuda_devices == 0:
        if cuda_ok:
            warnings.warn(
                "CUDA libraries loaded but no CUDA devices detected. "
                "Ensure NVIDIA GPU and drivers (520+) are installed.",
                RuntimeWarning
            )
        else:
            warnings.warn(
                "No CUDA devices detected and CUDA libraries may be incomplete.",
                RuntimeWarning
            )
    else:
        print("✓ CUDA support is working with bundled libraries!")
    
    # Re-export cv2 components
    from cv2 import *
    
except ImportError as e:
    print(f"Failed to import cv2: {e}")
    print("This may be due to missing system dependencies or incompatible libraries.")
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

def create_readme_file():
    """Create README for bundled distribution"""
    readme = '''# OpenCV with CUDA 12.8 Support (Bundled)

This wheel contains OpenCV 4.10.0 with CUDA 12.8 support and includes all necessary CUDA runtime libraries.

## Requirements

### System Requirements
- NVIDIA GPU with compute capability 8.0+ (RTX 30/40 series, A100, etc.)
- NVIDIA drivers 520+ (which support CUDA 12.x)
- Linux x86_64

### Python Requirements
- Python 3.8+
- numpy>=1.19.0 (automatically installed)

## Installation

```bash
pip install opencv_cuda-4.10.0+cuda12.8-*.whl
```

## Usage

```python
import opencv_cuda as cv2

# Check installation
print(f"OpenCV version: {cv2.__version__}")
print(f"CUDA devices: {cv2.cuda.getCudaEnabledDeviceCount()}")

# Use CUDA-accelerated functions
gpu_img = cv2.cuda_GpuMat()
gpu_img.upload(cpu_image)
# ... CUDA operations
```

## What's Included

This bundled wheel includes:
- OpenCV 4.10.0 libraries with CUDA support
- CUDA 12.8 runtime libraries
- All necessary NVIDIA Performance Primitives (NPP)
- cuBLAS, cuFFT, cuRAND libraries
- Python bindings

## Troubleshooting

1. **"No CUDA devices detected"**: Ensure NVIDIA drivers are installed and GPU is supported
2. **Import errors**: Try updating NVIDIA drivers to 520+
3. **Library conflicts**: This bundled version should avoid most conflicts, but you may need to uninstall other OpenCV packages first

## Size Note

This wheel is larger (~500MB+) because it includes all CUDA libraries.
For a smaller wheel that uses system CUDA, consider the lean version.
'''
    
    with open("README.md", "w") as f:
        f.write(readme)

def get_data_files():
    """Get list of data files to include"""
    data_files = []
    
    # Find all files in data directories
    pkg_dir = Path("opencv_cuda")
    
    if (pkg_dir / "data").exists():
        for root, dirs, files in os.walk(pkg_dir / "data"):
            for file in files:
                full_path = Path(root) / file
                # Convert to relative path from package directory
                rel_path = full_path.relative_to(pkg_dir)
                data_files.append(str(rel_path))
    
    # Add cv2 files and .so files in main directory
    for pattern in ["cv2/*", "cv2/**/*", "*.so"]:
        data_files.append(pattern)
    
    return data_files

def main():
    # Create package directory
    os.makedirs("opencv_cuda", exist_ok=True)
    os.makedirs("opencv_cuda/data", exist_ok=True)
    
    # Build/copy OpenCV libraries
    build_opencv_bundled()
    
    # Copy CUDA libraries
    copy_cuda_libraries()
    
    # Create bundled init file
    create_bundled_init()
    
    # Create README
    create_readme_file()
    
    # Get data files list
    data_files = get_data_files()
    
    setup(
        name="opencv-cuda",
        version="4.10.0+cuda12.8",
        description="OpenCV with CUDA 12.8 support (bundled with CUDA libraries)",
        long_description=open("README.md").read(),
        long_description_content_type="text/markdown",
        author="OpenCV Community", 
        author_email="opencv@opencv.org",
        url="https://opencv.org/",
        packages=["opencv_cuda"],
        package_data={
            "opencv_cuda": data_files
        },
        include_package_data=False,  # Use explicit package_data instead
        distclass=BinaryDistribution,
        cmdclass={'bdist_wheel': CustomBdistWheel},
        install_requires=[
            "numpy>=1.19.0",
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
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9", 
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12",
            "Topic :: Scientific/Engineering :: Image Processing",
            "Topic :: Software Development :: Libraries",
        ],
        zip_safe=False,
    )

if __name__ == "__main__":
    main()
