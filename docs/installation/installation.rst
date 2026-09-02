.. meta::
   :description: Install hipCIM from AMD PyPI or build from source
   :keywords: AMD-Ecosystem, life sciences, hipCIM installation

.. _installing-hipcim:

************************
Installing hipCIM
************************

You can install hipCIM from :ref:`AMD PyPI <install-package>`, from a
:ref:`Docker container <install-docker>`, or :ref:`from source <source-build>`.

System requirements:

+--------------+----------------+----------------+----------------------------------+
| ROCm version | Ubuntu version | Python version | AMD Instinct™ GPU (tested)       |
+==============+================+================+==================================+
| 10.0.0       | 24.04          | 3.12           | MI300X, MI325X, and MI355X       |
+--------------+----------------+----------------+----------------------------------+

.. note::

   Ubuntu 24.04 is the tested reference configuration and the required OS family
   for a :ref:`source build <source-build>`. The wheels target the
   ``manylinux_2_28`` standard and run on Linux distributions with glibc 2.28 or
   later.

.. _install-package:

Installing hipCIM using AMD PyPI
=================================

Install the prebuilt wheel from `AMD PyPI <https://pypi.amd.com/simple/>`_.
Compilation isn't required. 

If ROCm 10.0.0 is already installed at the system level or in the active
virtual environment, install ``amd-hipcim``. The package pulls in CuPy as
``amd-cupy`` from the public AMD index.

.. code:: shell

   pip install amd-hipcim --extra-index-url=https://pypi.amd.com/rocm-10.0.0/simple/

If ROCm 10.0.0 isn't installed, install ``amd-hipcim[rocm]``. The ``rocm`` extra
pulls in the ROCm runtime. Provide both the CuPy and ROCm public indexes.

.. code:: shell

   pip install "amd-hipcim[rocm]" \
     --extra-index-url=https://pypi.amd.com/rocm-10.0.0/simple/ \
     --extra-index-url=https://stable.repo.amd.com/rocm/whl-next/


Verify the installation:

.. code:: shell

   pip show -v amd-hipcim
   python -c "import cucim; print(cucim.__version__)"

Expected output includes ``26.06.00``.

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
===========================

Build hipCIM from source if you intend to develop for or contribute to the hipCIM project.

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
   the public pip index.

   .. code:: shell

      python3 -m venv hipcim_dev
      source hipcim_dev/bin/activate
      pip install --upgrade pip
      pip install "rocm[libraries,devel]" --index-url https://stable.repo.amd.com/rocm/whl-next/

3. Set the environment variables. ROCm 10.0.0 is a pip SDK, so resolve its root
   with ``rocm-sdk``.

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
     - Semicolon-separated list of GPU architectures to build for.

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
