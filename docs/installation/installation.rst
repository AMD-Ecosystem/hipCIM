.. meta::
   :description: Install hipCIM from AMD PyPI or build from source
   :keywords: AMD-Ecosystem, life sciences, hipCIM installation

.. _installing-hipcim:

************************
Installing hipCIM
************************

hipCIM can be installed using :ref:`AMD PyPI <install-package>` or it can be :ref:`built from source <source-build>`.

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

Setting up the environment
==========================

Set up the environment before installing hipCIM.

1. Optionally start an Ubuntu 24.04 Docker container.

   .. code:: shell

      docker run --cap-add=SYS_PTRACE --ipc=host --privileged=true   \
      --shm-size=128GB --network=host --device=/dev/kfd     \
      --device=/dev/dri --group-add video -it               \
      -v $HOME:$HOME  --name ${LOGNAME}_rocm                \
                                       ubuntu:24.04

2. Install the non-ROCm system dependencies.

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

3. Create a Python virtual environment and install the ROCm 10.0.0 SDK from the
   public pip index.

   .. code:: shell

      python3 -m venv hipcim_dev
      source hipcim_dev/bin/activate
      pip install --upgrade pip
      pip install "rocm[libraries,devel]" --index-url https://stable.repo.amd.com/rocm/whl-next/

4. Set the environment variables. Set ``AMDGPU_TARGETS`` to the GFX target for
   your GPU. Use only one value.

   .. code:: shell

      export ROCM_HOME=$(rocm-sdk path --root)
      # MI300X / MI325X
      export AMDGPU_TARGETS=gfx942
      # MI350X / MI355X
      # export AMDGPU_TARGETS=gfx950

.. _source-build:

Building hipCIM from source
===========================

Build hipCIM from source if you intend to develop for the library.

1. Install dependencies.

   .. code:: shell

      pip install --upgrade pip

2. Download the latest version of hipCIM from the git repository.

   .. code:: shell

      git clone https://github.com/AMD-Ecosystem/hipCIM.git
      cd hipCIM

3. Install the rest of the dependencies.

   .. code:: shell

      pip install -r ./requirements.txt

4. Build and install hipCIM.

   a. Build the base C++ libraries.

      .. code:: shell

         ./run_amd build_local cpp release

   b. Build the Python bindings.

      .. code:: shell

         ./run_amd build_local hipcim release

   c. Install the Python bindings.

      .. code:: shell

         # Install CuPy from the public AMD index first
         pip install amd-cupy --extra-index-url https://pypi.amd.com/rocm-10.0.0/simple/
         python3 -m pip install python/cucim --extra-index-url https://pypi.amd.com/rocm-10.0.0/simple/

5. Verify the installation.

   a. Generate test fixtures. You can run this step more than once. Existing
      files are left unchanged. ``run_amd`` also runs it automatically when you
      execute the C++ tests.

      .. code:: shell

         ./test_data/gen_images.sh

   b. Run the tests in the base C++ libraries. The ``release`` argument is
      accepted but unused by ``test_cpp``.

      .. code:: shell

         ./run_amd test cpp release

   c. Run the Python tests.

      .. code:: shell

         ./run_amd test_python

.. _install-package:

Installing hipCIM using AMD PyPI
================================

hipCIM users who don't intend to develop for the library can install hipCIM from
`AMD PyPI <https://pypi.amd.com/simple/>`_ using the ROCm 10.0.0 index URL in the
installation commands.

.. note::

   The prebuilt ``amd-hipcim`` wheels are built against the `manylinux_2_28
   <https://github.com/pypa/manylinux>`_ standard and repaired with
   ``auditwheel``. They're portable across Linux distributions with glibc 2.28
   or later and Python 3.12. Supported distributions include Ubuntu 20.04 and
   later, Debian 10 and later, RHEL 8 and later, AlmaLinux 8 and later, Rocky
   Linux 8 and later, and SUSE.

1. Install hipCIM.

   If ROCm is already installed, install ``amd-hipcim``.

   .. code:: shell

      pip install amd-hipcim --extra-index-url=https://pypi.amd.com/rocm-10.0.0/simple/

   If ROCm isn't already installed, install ``amd-hipcim[rocm]``.

   .. code:: shell

      pip install "amd-hipcim[rocm]" \
        --extra-index-url=https://pypi.amd.com/rocm-10.0.0/simple/ \
        --extra-index-url=https://stable.repo.amd.com/rocm/whl-next/

2. Verify the installation.

   .. code:: shell

      pip show -v amd-hipcim

   Expected ``pip show`` output for a ROCm 10.0.0 wheel install:

   .. code:: shell

      Name: amd-hipcim
      Version: 26.06.00
      Summary: hipCIM - an extensible toolkit designed to provide GPU accelerated I/O, computer vision & image processing primitives for N-Dimensional images with a focus on biomedical imaging.
      Home-page: https://rocm.docs.amd.com/projects/hipCIM/en/latest/
      Author: AMD Corporation
      Author-email:
      License: Apache 2.0
      Location: /scratch/integration/hipCIM/hipcim_dev/lib/python3.12/site-packages
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

.. _rocjpeg-runtime:

rocJPEG and the amdgpu VA-API driver
========================================================

rocJPEG isn't shipped inside the ``amd-hipcim`` wheel. It's supplied with a ROCm installation. The hipCIM installation won't fail if rocJPEG is missing, but slide formats won't open without rocJPEG's ``librocjpeg.so.1`` and its matching amdgpu VA-API driver.

At load time, if ``librocjpeg.so.1`` or its VA-API driver can't be loaded, the
hipslide plugin fails to register. hipCIM logs a warning and continues with the
remaining plugins. NIfTI and DICOM reads can still succeed.

.. note::

   If rocJPEG still fails to load after import, add the ROCm SDK library
   directory to the loader path and point libva at the bundled amdgpu driver.

   .. code:: shell

      # pip/venv ROCm: the _rocm_sdk_devel/lib directory that holds librocjpeg.so.1
      # and the amdgpu VA-API driver. For a classic install use ${ROCM_PATH}/lib.
      export ROCM_LIB=$(python -c "import sysconfig, os; print(os.path.join(sysconfig.get_paths()['purelib'], '_rocm_sdk_devel', 'lib'))")

      export LD_LIBRARY_PATH="${ROCM_LIB}${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
      export LIBVA_DRIVERS_PATH="${ROCM_LIB}"
      export LIBVA_DRIVER_NAME=amdgpu

Sample usage
===============

Use this sample to get started with hipCIM.

.. code:: shell

   ./test_data/gen_images.sh

The sample opens the generated image with ``CuImage`` and reads a region on the GPU.

The Python code opens the generated image.

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
