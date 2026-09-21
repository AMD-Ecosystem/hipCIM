.. meta::
   :description: The hipCIM library is a robust open-source solution developed to significantly accelerate computer vision and image processing capabilities
   :keywords: AMD-Ecosystem, life sciences, hipCIM installation

.. _installing-hipcim:

*******************
Installing hipCIM
*******************

This topic discusses how to install hipCIM using the following options:

- :ref:`Recommended: AMD PyPI (for users) <install-package>`

- :ref:`Docker (recommended for isolated environments) <install-docker>`

- :ref:`Build from source (for developers) <source-build>`


System requirements
=======================

+--------------+----------------+----------------+----------------------------------+
| ROCm version | Ubuntu version | Python version | AMD Instinct™ GPU                |
+==============+================+================+==================================+
| 10.0.0       | 24.04          | 3.12           | MI300X, MI325X, and MI355X       |
+--------------+----------------+----------------+----------------------------------+

.. note::

   The prebuilt ``amd-hipcim`` wheels target ``manylinux_2_28`` (glibc 2.28) and run on any glibc >= 2.28 Linux distribution with Python 3.12. However, hipCIM has only been tested and validated on Ubuntu 24.04. 
   
.. _install-package:

Installing hipCIM using AMD PyPI 
==================================

Packaged versions of hipCIM and its dependencies are distributed via `AMD PyPI <https://pypi.amd.com/simple/>`_. This section discusses how to install hipCIM using this package index. hipCIM users should use this installation method. hipCIM developers should use :ref:`source-build`.

1. Install hipCIM. There are two prebuilt options:

   - If ROCm 10.0.0 is already available (installed at the system level or in the
     active virtual environment), install ``amd-hipcim``. It pulls in CuPy
     (``amd-cupy``), a hipCIM dependency, from the public AMD index:

     .. code-block:: shell

      pip install amd-hipcim --extra-index-url=https://pypi.amd.com/rocm-10.0.0/simple/

   - If ROCm 10.0.0 is not installed (no system ROCm and none in the virtual
     environment), install ``amd-hipcim[rocm]``. The ``rocm`` extra additionally
     pulls in the ROCm runtime, so provide both the CuPy and ROCm public indexes:

     .. code-block:: shell

      pip install "amd-hipcim[rocm]" \
        --extra-index-url=https://pypi.amd.com/rocm-10.0.0/simple/ \
        --extra-index-url=https://repo.amd.com/rocm/whl-multi-arch/

2. Verify the installation.

   .. code-block:: shell

      pip show -v amd-hipcim

   Expected output:

   .. code-block:: shell

      Name: amd-hipcim
      Version: 25.10.0
      Summary: hipCIM - an extensible toolkit designed to provide GPU accelerated I/O, computer vision & image processing primitives for N-Dimensional images with a focus on biomedical imaging.
      Home-page: https://rocm.docs.amd.com/projects/hipCIM/en/latest/
      Author: AMD Corporation
      Author-email:
      License: Apache 2.0
      Location: /scratch/integration/hipCIM/hipcim_dev/lib/python3.10/site-packages
      Requires: amd-cupy, click, lazy-loader, numpy, scikit-image, scipy
      Required-by:
      Metadata-Version: 2.4
      Installer: pip
      Classifiers:
         Development Status :: 4 - Beta
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


.. _install-docker:

Installing hipCIM using Docker
===============================

Use a plain Ubuntu 24.04 Docker container for hipCIM.

1. Start an Ubuntu 24.04 Docker container.

   .. code:: shell

      docker run --cap-add=SYS_PTRACE --ipc=host --privileged=true \
        --shm-size=128GB --network=host --device=/dev/kfd \
        --device=/dev/dri --group-add video -it \
        -v $HOME:$HOME --name ${LOGNAME}_rocm ubuntu:24.04

2. Inside the container, install ``amd-hipcim[rocm]``. ROCm isn't present in
   this image.

   .. code:: shell

      pip install "amd-hipcim[rocm]" \
        --extra-index-url=https://pypi.amd.com/rocm-10.0.0/simple/ \
        --extra-index-url=https://stable.repo.amd.com/rocm/whl-next/

.. _source-build:

Building hipCIM from source
=============================

To build hipCIM from source, follow the steps given in this section. hipCIM developers should use this installation method. hipCIM users should use the :ref:`Installing hipCIM using AMD PyPI <install-package>`

1. Install the non-ROCm system dependencies. 

   .. code:: shell

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

2. Create a Python virtual environment and install the ROCm 10.0.0 SDK from
   the public pip index. ``AMDGPU_TARGETS`` lists the architectures to build
   for. The release targets ``gfx942`` (MI300X and MI325X) and ``gfx950``
   (MI350X and MI355X), and both need their own ``device-gfx*`` extras, which
   carry the GPU code objects.

   .. code:: shell

      python3 -m venv hipcim_dev
      source hipcim_dev/bin/activate
      pip install --upgrade pip
      pip install "rocm[libraries,devel,device-gfx942,device-gfx950]" --index-url https://stable.repo.amd.com/rocm/whl-next/

   Ensure that a wheel exists for the target architecture:

   .. code:: shell

      pip list | grep rocm-sdk-device

   To build for a single GPU, align ``AMDGPU_TARGETS`` with the device extra.
   For example, for a gfx950 target, use ``AMDGPU_TARGETS=gfx950`` with
   ``rocm[libraries,devel,device-gfx950]``. Setting ``AMDGPU_TARGETS`` without
   using its corresponding device wheel will result in binaries that won't run.

   If a device wheel is added or removed later, run ``rocm-sdk init`` to relink
   it.

3. Set the environment variables.

   .. code:: shell

      export ROCM_HOME=$(rocm-sdk path --root)
      export AMDGPU_TARGETS="gfx942;gfx950"

4. Clone the repository and build hipCIM.

   .. code:: shell

      git clone https://github.com/AMD-Ecosystem/hipCIM.git
      cd hipCIM
      pip install -r ./requirements.txt
      ./run_amd build_local cpp release
      ./run_amd build_local hipcim release
      pip install amd-cupy --extra-index-url https://pypi.amd.com/rocm-10.0.0/simple/
      python3 -m pip install python/cucim --extra-index-url https://pypi.amd.com/rocm-10.0.0/simple/

5. Run the tests.

   .. code:: shell

      ./run_amd test cpp release
      ./run_amd test_python

.. _rocjpeg-runtime:

rocJPEG and the amdgpu VA-API driver
======================================

Whole slide image decode for SVS and TIFF runs through the ``cuslide`` plugin.
That plugin has a load-time dependency on ``librocjpeg.so.1`` and a matching
amdgpu VA-API driver. If either the library or the driver can't be loaded, the ``cuslide`` plugin
fails to register. CPU fallback for SVS and TIFF is then unavailable, and
hipCIM raises ``Cannot find a plugin to handle 'slide.svs'!``.

When ROCm 10.0.0 is installed from the AMD pip index, both libraries ship in
the ROCm SDK wheels under ``_rocm_sdk_devel/lib``. hipCIM preloads them on
import. ``cucim.clara`` preloads ``amdhip64`` and ``rocjpeg``.

For a classic ``/opt/rocm`` install or a custom layout, set the following environment variables to ensure that the driver and library are in the path:

.. code:: shell

   export LD_LIBRARY_PATH="${ROCM_PATH}/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
   export LIBVA_DRIVERS_PATH="${ROCM_PATH}/lib"
   export LIBVA_DRIVER_NAME=amdgpu

Environment variables
======================

These environment variables affect a source build and a custom ROCm layout.

.. list-table::
   :header-rows: 1
   :widths: 28 28 44

   * - Variable
     - Default
     - Purpose
   * - ``ROCM_HOME``
     - Output of ``rocm-sdk path --root``.
     - Path to the ROCm installation when ROCm 10.0.0 is a pip SDK.
   * - ``AMDGPU_TARGETS``
     - ``gfx942;gfx950``
     - Semicolon-separated list of GPU architectures to build for. Every listed
       architecture needs its ``rocm-sdk-device-*`` wheel installed.

Sample usage
============

``CuImage`` opens a generated image and reads a region on the GPU.

.. code:: shell

   ./test_data/gen_images.sh

.. code-block:: python

   from cucim import CuImage

   img = CuImage("test_data/generated/tiff_stripe_32x32_16.tif")
   resolutions = img.resolutions
   level_dimensions = resolutions["level_dimensions"]
   level_count = resolutions["level_count"]

   print(resolutions)
   print(level_count)
   print(level_dimensions)

   region = img.read_region([0,0], level_dimensions[level_count - 1], level_count - 1, device="cuda")
   print(region.device)

Expected output:

.. code:: shell

   {'level_count': 1, 'level_dimensions': ((32, 32),), 'level_downsamples': (1.0,), 'level_tile_sizes': ((16, 16),)}
   1
   ((32, 32),)
   cuda
