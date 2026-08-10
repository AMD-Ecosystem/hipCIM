.. meta::
   :description: The hipCIM library is a robust open-source solution developed to significantly accelerate computer vision and image processing capabilities
   :keywords: ROCm-LS, life sciences, hipCIM installation

.. _installing-hipcim:

===================
Installing hipCIM
===================

This topic discusses how to install hipCIM using the following options:

- :ref:`Build from source (for developers) <source-build>`

- :ref:`Recommended: AMD PyPI (for users) <install-package>`

System requirements
********************

+--------------+----------------+----------------+----------------------------------+
| ROCm version | Ubuntu version | Python version | AMD Instinct GPU (tested)        |
+==============+================+================+==================================+
| 10.0.0       | 24.04          | 3.12           | MI300X, MI325X, MI350X, MI355X   |
+--------------+----------------+----------------+----------------------------------+

.. note::

   The Ubuntu 24.04 entry above is the tested reference configuration (and the
   required OS family for a :ref:`source build <source-build>`). The prebuilt
   ``amd-hipcim`` wheels target ``manylinux_2_28`` (glibc 2.28) and run on any
   glibc >= 2.28 Linux distribution, as described under :ref:`install-package`.

Setting up the environment
***************************

To set up the environment for installing hipCIM, follow these steps:

1. Optional: Use ROCm Docker to get started.

   ROCm 10.0 is installed from the pip index (see step 3), so a plain Ubuntu
   24.04 container can be used:

   .. code-block:: shell

      docker run --cap-add=SYS_PTRACE --ipc=host --privileged=true   \
      --shm-size=128GB --network=host --device=/dev/kfd     \
      --device=/dev/dri --group-add video -it               \
      -v $HOME:$HOME  --name ${LOGNAME}_rocm                \
                                       ubuntu:24.04

   For bare metal, skip this step.

2. Install the non-ROCm system dependencies (ROCm itself is installed from the
   public pip index in step 3):

   .. code-block:: shell

      apt-get update && \
      apt-get install -y software-properties-common lsb-release gnupg curl && \
      apt-key adv --fetch-keys https://apt.kitware.com/keys/kitware-archive-latest.asc && \
      add-apt-repository -y "deb https://apt.kitware.com/ubuntu/ $(lsb_release -cs) main" && \
      apt-get update && \
      apt-get install -y git wget gcc g++ ninja-build git-lfs \
                     yasm libopenslide-dev libwebp-dev libzstd-dev \
                     python3 python3-venv python3-dev libpython3-dev cmake

3. Create the Python virtual environment and install the ROCm 10.0 SDK from the
   public pip index into it.

   .. code-block:: shell

      python3 -m venv hipcim_dev
      source hipcim_dev/bin/activate
      pip install --upgrade pip
      pip install "rocm[libraries,devel]" --index-url https://repo.amd.com/rocm/whl-multi-arch/

4. Set the environment variables. ROCm 10.0 is a pip SDK, so resolve its root
   with ``rocm-sdk``:

   .. code-block:: shell

      export ROCM_HOME=$(rocm-sdk path --root)
      export AMDGPU_TARGETS="gfx942;gfx950"

.. _source-build:

Building hipCIM from source
****************************

To build hipCIM from source, follow the steps given in this section. hipCIM developers should use this installation method. hipCIM users should use the :ref:`Installing hipCIM using AMD PyPI <install-package>`

1. Install dependencies.

   .. code-block:: shell

      pip install --upgrade pip

2. Download the latest version of hipCIM from the git repository.

   .. code-block:: shell

      git clone git@github.com:ROCm-LS/hipCIM.git
      cd hipCIM

3. Install the rest of the dependencies.

   .. code-block:: shell

      pip install -r ./requirements.txt

4. Build and install hipCIM.

   To build the hipCIM library on a ROCm-based AMD system using the development environment, follow these steps:

   1. Build the base C++ libraries.

      .. code-block:: shell

         ./run_amd build_local cpp release

   2. Build the Python bindings.

      .. code-block:: shell

         ./run_amd build_local hipcim release

   3. Install the Python bindings.

      .. code-block:: shell

         # Install CuPy from the public AMD index first
         pip install amd-cupy --extra-index-url https://pypi.amd.com/rocm-10.0.0/simple/
         python3 -m pip install python/cucim --extra-index-url https://pypi.amd.com/rocm-10.0.0/simple/

6. Verify the installation.

   To verify the installation, follow these steps:

   1. Execute the tests in the base C++ libraries.

      .. code-block:: shell

         ./run_amd test cpp release

   2. Execute the Python tests.

      .. code-block:: shell

         ./run_amd test_python

.. _install-package:

Installing hipCIM using AMD PyPI (recommended)
***********************************************

Packaged versions of hipCIM and its dependencies are distributed via `AMD PyPI <https://pypi.amd.com/simple/>`_. This section discusses how to install hipCIM using this package index. hipCIM users should use this installation method. hipCIM developers should use the :ref:`source-build`.

.. note::

   The prebuilt ``amd-hipcim`` wheels are built against the `manylinux_2_28
   <https://github.com/pypa/manylinux>`_ standard (glibc 2.28) and repaired with
   ``auditwheel``, so they are portable across any glibc >= 2.28 Linux
   distribution (for example Ubuntu 20.04+, Debian 10+, RHEL/AlmaLinux/Rocky 8+,
   and SUSE), not just Ubuntu 24.04. Any distribution providing Python 3.12 and
   glibc >= 2.28 works; the Ubuntu 24.04 steps are one convenient, tested setup.

1. Install hipCIM. There are two prebuilt options:

   - If ROCm 10.0 is already available (installed at the system level or in the
     active virtual environment), install ``amd-hipcim``. It pulls in CuPy
     (``amd-cupy``), a hipCIM dependency, from the public AMD index:

     .. code-block:: shell

      pip install amd-hipcim --extra-index-url=https://pypi.amd.com/rocm-10.0.0/simple/

   - If ROCm 10.0 is not installed (no system ROCm and none in the virtual
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
         Source, https://github.com/ROCm-LS/hipCIM
         Tracker, https://github.com/ROCm-LS/hipCIM/issues

Getting started
****************

Here is a sample Python code and its expected output to help you get started.

- Sample code:

  .. code-block:: shell

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

- Expected output:

  .. code-block:: shell

   {'level_count': 1, 'level_dimensions': ((601, 81),), 'level_downsamples': (1.0,), 'level_tile_sizes': ((0, 0),)}
   1
   ((601, 81),)
   [Warning] Loading image('sample_image/oxford.tif') with a slow-path. The pixel format of the loaded image would be RGBA (4 channels) instead of RGB!
   cuda
