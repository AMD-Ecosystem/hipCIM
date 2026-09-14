# <div align="left">&nbsp;cuCIM/hipCIM&nbsp;</div>

## hipCIM 
hipCIM is a [HIP](https://github.com/ROCm/hip) port of the [cuCIM](https://github.com/rapidsai/cucim) library under the [RAPIDS](https://github.com/rapidsai) ecosystem.
This library is an extensible toolkit designed to provide GPU accelerated I/O, computer vision & image processing primitives for N-Dimensional images with a focus on biomedical imaging.

### Resources
- [hipCIM API reference](https://rocm.docs.amd.com/projects/hipCIM/en/latest/reference/hipcim/index.html#hipcim-reference)

### Install hipCIM on ROCm 10.0 via AMD PyPI

> **Note:** The prebuilt `amd-hipcim` wheels are built against the [`manylinux_2_28`](https://github.com/pypa/manylinux) standard (glibc 2.28) and repaired with `auditwheel`, so they are portable across any glibc ≥ 2.28 Linux distribution (for example Ubuntu 20.04+, Debian 10+, RHEL/AlmaLinux/Rocky 8+, and SUSE), not just Ubuntu 24.04. The Ubuntu 24.04 steps below are one convenient, tested setup; any distribution providing Python 3.12 and glibc ≥ 2.28 works.

- [Optional step] ROCm 10.0 is installed from the pip index below, so a plain Ubuntu 24.04 container can be used
	```
	docker run --cap-add=SYS_PTRACE --ipc=host --privileged=true   \
         --shm-size=128GB --network=host --device=/dev/kfd     \
         --device=/dev/dri --group-add video -it               \
         -v $HOME:$HOME  --name ${LOGNAME}_rocm                \
     ubuntu:24.04
	```
- Install required (non-ROCm) system dependencies
	```
    apt-get update && \
        apt-get install -y lsb-release gnupg curl ca-certificates && \
        curl -fsSL https://apt.kitware.com/keys/kitware-archive-latest.asc \
            | gpg --dearmor -o /usr/share/keyrings/kitware-archive-keyring.gpg && \
        echo "deb [signed-by=/usr/share/keyrings/kitware-archive-keyring.gpg] https://apt.kitware.com/ubuntu/ $(lsb_release -cs) main" \
            > /etc/apt/sources.list.d/kitware.list && \
        apt-get update && \
        apt-get install -y git wget gcc g++ ninja-build git-lfs \
                      yasm libopenslide-dev libwebp-dev libzstd-dev \
                      python3 python3-venv python3-dev libpython3-dev cmake
	```

- Create a python3 virtual environment and install the ROCm 10.0 SDK from the public pip index
	```
	python3 -m venv hipcim_dev
	source hipcim_dev/bin/activate
	pip install --upgrade pip
	pip install "rocm[libraries,devel]" --index-url https://stable.repo.amd.com/rocm/whl-next/
  ```

- Setup environment variables
  ```
  export ROCM_HOME=$(rocm-sdk path --root)
  #For MI300X / MI325X (gfx942)
  export AMDGPU_TARGETS=gfx942
  #For MI350X / MI355X (gfx950)
  export AMDGPU_TARGETS=gfx950
	```
- Install hipcim. There are two options:

  **Option 1 — ROCm already available** (installed at the system level or via the ROCm SDK venv step above). Installs CuPy (`amd-cupy`) as a hipCIM dependency:
  ```
  pip install amd-hipcim --extra-index-url=https://pypi.amd.com/rocm-10.0.0/simple/
  ```

  **Option 2 — ROCm not installed.** The `[rocm]` extra pulls in ROCm and CuPy, so provide both public indexes (you can skip the ROCm SDK install step above):
  ```
  pip install "amd-hipcim[rocm]" \
    --extra-index-url=https://pypi.amd.com/rocm-10.0.0/simple/ \
    --extra-index-url=https://stable.repo.amd.com/rocm/whl-next/
  ```

- Verify installation
  ```
  pip show -v amd-hipcim
  ```
- Expected output
  ```
  Version details: (26, 6, 1, 'dev50', 'g03857c672')
  Name: amd-hipcim
  Version: 26.6.0
  Summary: hipCIM - an extensible toolkit designed to provide GPU accelerated I/O, computer vision & image processing primitives for N-Dimensional images with a focus on biomedical imaging.
  Home-page: https://rocm.docs.amd.com/projects/hipCIM/en/latest/
  Author: AMD Corporation
  Author-email: 
  License: Apache 2.0
  Location: /tmp/hipcim-venv/lib/python3.12/site-packages
  Requires: amd-cupy, click, lazy-loader, numpy, scikit-image, scipy
  Required-by: 
  Metadata-Version: 2.4
  Installer: pip
  Classifiers:
    Development Status :: 5 - Production/Stable
    Intended Audience :: Developers
    Intended Audience :: Education
    Intended Audience :: Science/Research
    Intended Audience :: Healthcare Industry
    Topic :: Scientific/Engineering
    Operating System :: POSIX :: Linux
    Environment :: Console
    Environment :: GPU :: AMD Instinct :: MI300
    License :: OSI Approved :: Apache Software License
    Programming Language :: C++
    Programming Language :: Python
    Programming Language :: Python :: 3
  Entry-points:
    [console_scripts]
    cucim = cucim.clara.cli:main
  Project-URLs:
    Homepage, https://rocm.docs.amd.com/projects/hipCIM/en/latest/
    Documentation, https://rocm.docs.amd.com/projects/hipCIM/en/latest/
    Source, https://github.com/AMD-Ecosystem/hipCIM
    Tracker, https://github.com/AMD-Ecosystem/hipCIM/issues
  ```


 - Run a sample program
   ```python3
    from cucim import CuImage
    img = CuImage("sample_image/oxford.tif")
    resolutions = img.resolutions
    level_dimensions = resolutions["level_dimensions"]
    level_count = resolutions["level_count"]
    print(resolutions)
    print(level_count)
    print(level_dimensions)
    region = img.read_region([0,0], level_dimensions[level_count - 1], level_count - 1, device="cuda")
    print(region.device)
   ```

 - Output
   ```
    {'level_count': 1, 'level_dimensions': ((601, 81),), 'level_downsamples': (1.0,), 'level_tile_sizes': ((0, 0),)}
    1
    ((601, 81),)
    [Warning] Loading image('oxford.tif') with a slow-path. The pixel format of the loaded image would be RGBA (4 channels) instead of RGB!
    cuda
   ```


### Build hipCIM on ROCm 10.0 from source
Please use the below steps to build the hipCIM library on a ROCm based MI300X/MI325X/MI350X/MI355X system from source.

- [Optional step] ROCm 10.0 is installed from the pip index below, so a plain Ubuntu 24.04 container can be used
	```
    docker run --cap-add=SYS_PTRACE --ipc=host --privileged=true   \
         --shm-size=128GB --network=host --device=/dev/kfd     \
         --device=/dev/dri --group-add video -it               \
         -v $HOME:$HOME  --name ${LOGNAME}_rocm                \
     ubuntu:24.04
    ```

- Install required (non-ROCm) system dependencies
  	```
    apt-get update && \
        apt-get install -y lsb-release gnupg curl ca-certificates && \
        curl -fsSL https://apt.kitware.com/keys/kitware-archive-latest.asc \
            | gpg --dearmor -o /usr/share/keyrings/kitware-archive-keyring.gpg && \
        echo "deb [signed-by=/usr/share/keyrings/kitware-archive-keyring.gpg] https://apt.kitware.com/ubuntu/ $(lsb_release -cs) main" \
            > /etc/apt/sources.list.d/kitware.list && \
        apt-get update && \
        apt-get install -y git wget gcc g++ ninja-build git-lfs \
                      yasm libopenslide-dev libwebp-dev libzstd-dev \
                      python3 python3-venv python3-dev libpython3-dev cmake
	```

- Checkout the latest version of hipCIM from git
    ```
    git clone git@github.com:AMD-Ecosystem/hipCIM.git
    cd hipCIM
    ```

- Create a python3 virtual environment, install the ROCm 10.0 SDK and python dependencies
	```
	python3 -m venv hipcim_dev
	source hipcim_dev/bin/activate
	pip install --upgrade pip
	pip install "rocm[libraries,devel]" --index-url https://stable.repo.amd.com/rocm/whl-next/
	pip install -r ./requirements.txt
	```

- Setup environment variables
  ```
  export ROCM_HOME=$(rocm-sdk path --root)
  #For MI300X / MI325X (gfx942)
  export AMDGPU_TARGETS=gfx942
  #For MI350X / MI355X (gfx950)
  export AMDGPU_TARGETS=gfx950
  ```

- Build the cpp base libraries

  ```bash
  ./run_amd build_local cpp release
  ```

- Build the python3 bindings

  ```bash
  ./run_amd build_local hipcim release
  ```

- Install the hipCIM python3 package (CuPy resolves from the public AMD index)
  ```bash
  pip install amd-cupy --extra-index-url https://pypi.amd.com/rocm-10.0.0/simple/
  python3 -m pip install python/cucim --extra-index-url https://pypi.amd.com/rocm-10.0.0/simple/
  ```

- **[First time only]** Generate test data files
  ```bash
  # Generate test TIFF images required for C++ tests
  ./test_data/gen_images.sh
  ```

- Run all cpp unit tests
  ```bash
  ./run_amd test cpp release
  ```

- Run all python3 unit tests
  ```bash
  ./run_amd test_python
  ```


### Code Coverage

hipCIM supports comprehensive code coverage for both C++ and Python components. For detailed information about generating and understanding code coverage reports, please refer to [scripts/README.md](scripts/README.md#code-coverage).

Quick commands:
- **C++ Coverage**: `./run_amd cpp_coverage`
- **Python Coverage**: Automatically generated with `./run_amd test_python`

## Contributing Guide

Contributions to hipCIM are more than welcome!
Please review the [CONTRIBUTING.md](https://github.com/AMD-Ecosystem/hipCIM/CONTRIBUTING.md) file for information on how to contribute code and issues to the project.

## Acknowledgments

Without awesome third-party open source software, this project wouldn't exist.

Please find [LICENSE-3rdparty.md](LICENSE-3rdparty.md) to see which third-party open source software
is used in this project.

## License

Apache-2.0 License (see [LICENSE](LICENSE) file).

Copyright (c) 2020-2026, NVIDIA CORPORATION.
Modifications Copyright (C) 2024-2026 Advanced Micro Devices, Inc. All rights reserved.
