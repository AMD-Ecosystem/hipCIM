.. meta::
   :description: New features, bug fixes, and known limitations in hipCIM 26.06.00
   :keywords: hipCIM, release notes, hipCIM 26.06.00, ROCm, AMD

.. _whats-new:

********************************
What's new in hipCIM 26.06.00
********************************

hipCIM 26.06.00 is based on upstream cuCIM 26.06.00. This release adds medical
imaging readers, multi-format TIFF support, and rocJPEG performance improvements.

New features
============

OME-TIFF and multi-page TIFF support
-------------------------------------

Prior releases rejected any TIFF file with more than one full-resolution IFD
with ``more than one image with Subfile Type 0``. That blocked the OME-TIFF format
family: Z-stacks, time-series, channel-split files, and high-content screening
plates.

hipCIM 26.06.00 removes this restriction. Multi-IFD TIFFs open as a flat page
list, with each Subfile-Type-0 IFD exposed as a level.

Empirical impact measured against the Bio-Formats / OME canonical corpus of
2,703 files:

.. list-table::
   :header-rows: 1
   :widths: 40 12 12 12

   * - Corpus segment
     - Files
     - Before
     - After
   * - OME-TIFF/BBBC, high-content screening
     - 2,304
     - 0/2,304
     - 2,304/2,304
   * - OME-TIFF/4D Z+T
     - 86
     - 0/86
     - 86/86
   * - OME-TIFF/3D-Z
     - 2
     - 0/2
     - 2/2
   * - OME-TIFF/other
     - 16
     - 2/16
     - 16/16
   * - Vectra-QPTIFF
     - 6
     - 0/6
     - 4/6
   * - Total
     - 2,703
     - 22 of 2,703, 0.8%
     - 2,442 of 2,703, 90.3%

The segment rows break out the OME-TIFF-specific portions of the corpus, 2,414
files in total. The totals cover all 2,703 files, including formats that aren't
listed separately.

Multi-IFD ordering is deterministic: IFDs sort by width descending, then height
descending, then original index ascending. Each IFD carries a stable
``hash_value()`` used as the tile-cache key.

.. note::

   This release exposes multi-IFD files as a flat level list with ``dims="YXC"``.
   True Z/T axis support from OME-XML metadata and SubIFD pyramid traversal are
   planned for a future release.

NIfTI-1 reader
----------------

``CuImage`` opens NIfTI-1 volumetric files (``.nii``, ``.nii.gz``) directly,
without nibabel, DCMTK, or any external medical imaging library.

- Hand-rolled 348-byte header parser conforming to the NIfTI-1 specification
- Automatic endianness detection and byte-swap
- Gzip decompression via libdeflate
- Supported data types: int8, uint8, int16, uint16, int32, uint32, int64,
  uint64, float32, float64
- Coordinate system reported as ``RAS``. Dimensions are ``ZYXC`` or ``TZYXC``.
- Voxel spacing taken from the NIfTI-1 ``pixdim`` field

.. code-block:: python

   from cucim import CuImage

   vol = CuImage("brain.nii.gz")
   print(vol.shape)      # e.g. [182, 218, 182, 1]
   print(vol.dims)       # e.g. "ZYXC"
   print(vol.dtype)      # e.g. float32
   print(vol.spacing())  # voxel size in mm, in dims order
   print(vol.coord_sys)  # "RAS"

Pixel data is read with ``read_region()``, which returns an object supporting
the DLPack and array interfaces:

.. code-block:: python

   import numpy as np

   arr = np.asarray(vol.read_region())
   print(arr.shape, arr.dtype)

DICOM Phase 1 reader
----------------------

``CuImage`` opens single-frame DICOM files (``.dcm``) without DCMTK or GDCM. A
minimal hand-rolled tag parser reads the DICOM tags needed to reconstruct pixel
data and spatial metadata.

Supported in Phase 1:

- Transfer syntaxes: Explicit VR Little-Endian, Implicit VR Little-Endian,
  uncompressed
- Compressed transfer syntaxes: JPEG Baseline (1.2.840.10008.1.2.4.50) and
  JPEG 2000 (1.2.840.10008.1.2.4.90). Enabled by default. Prebuilt
  ``amd-hipcim`` wheels ship with ``CUMED_DICOM_COMPRESSED`` ON.
- Photometric interpretations: MONOCHROME1, MONOCHROME2, RGB, YBR_FULL,
  YBR_FULL_422
- Pixel representations: unsigned and signed integer
- Coordinate system reported as ``LPS``. Spacing comes from ``PixelSpacing`` and
  ``SliceThickness`` tags

Not yet supported in Phase 1: multi-frame DICOM, DICOM-SEG, DICOM-WSI pyramid,
DICOM SR.

rocJPEG handle pool
-------------------

rocJPEG decode handles are managed by a process-level singleton pool
(``RocJpegHandlePool``). Previously, every ``read_region()`` call created and
destroyed a full ``rocJpegCreate()`` / ``rocJpegDestroy()`` cycle. Pooling
reuses handles across calls. The benefit is largest for single and small reads.
Batched reads share one handle across the whole batch and see a more modest
gain.

.. list-table::
   :header-rows: 1
   :widths: 40 16 16 12

   * - Metric
     - Before pool
     - With pool
     - Speedup
   * - Single 256 px ``read_region`` with ``device="cuda"``
     - 3.76 ms
     - 0.515 ms
     - ~7.3×
   * - 64-tile batch read, total time
     - 8.36 ms
     - 4.50 ms
     - ~1.9×
   * - CPU reference (single 256 px)
     - 0.18 ms
     - 0.18 ms
     - n/a

Benchmarked on AMD Instinct MI350X with ROCm 10.0.0. The test used CMU-1.svs,
level 0, 256 px tiles, distinct tiles per iteration, mean of 3 runs. These are
representative internal benchmarks, not in-repository CI results.

Process-level GPU tile cache
----------------------------

Decoded tiles are cached in a process-level LRU cache keyed on IFD location. On
overlapping or repeated patch reads, tiles can return from the cache without
re-decoding. See the `hipCIM introductory blog post
<https://rocm.blogs.amd.com/software-tools-optimization/hipcim-intro/README.html>`_
for representative throughput measurements on cached workloads.

New cucim.skimage GPU operators
--------------------------------

Several scikit-image operators are newly available as GPU-accelerated
implementations in ``cucim.skimage``:

- Restoration: ``rolling_ball`` background subtraction, with a hipCIM-specific
  ``downscale`` parameter for large kernels
- Morphology extrema: ``h_maxima``, ``h_minima``, ``local_maxima``,
  ``local_minima``
- Transform: batch and multi-channel warp interpolation optimization for
  ``warp``, ``resize``, and ``rotate``

.. code-block:: python

   from cucim.skimage.restoration import rolling_ball

   # downscale is keyword-only. Values >1 shrink the image before processing,
   # then upscale the result back to the original size.
   background = rolling_ball(image, radius=100, downscale=2)

Portable manylinux wheels
-------------------------

Prebuilt ``amd-hipcim`` wheels target the ``manylinux_2_28`` standard (glibc
2.28) and are repaired with ``auditwheel``. Wheels run on any glibc >= 2.28
Linux distribution, for example Ubuntu 20.04+, Debian 10+, RHEL/AlmaLinux/Rocky
8+, and SUSE, rather than requiring Ubuntu 24.04.

Graceful plugin degradation
---------------------------

When a plugin fails to load at runtime because ``librocjpeg.so.1`` isn't
installed, hipCIM logs a warning and continues with the remaining plugins. NIfTI and DICOM reads can succeed even on hosts where GPU
slide-format libraries are absent.

Bug fixes
=========

The following table lists bug fixes in this release.

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Area
     - Fix
   * - rocJPEG batch path
     - Fixed a SIGSEGV triggered by scattered or out-of-range ``read_region()``
       calls
   * - rocJPEG VRAM allocation
     - Fixed an OOM abort when device memory was nearly exhausted during batch
       allocation
   * - JP2K GPU path
     - Fixed a GPU abort where JPEG 2000 tiles were incorrectly routed to the
       GPU decode path. They now decode to host memory first.
   * - RGB colour output
     - Fixed blue/red channel swap on RGB-native images in the host-input GPU
       decode path
   * - rocJPEG error handling
     - rocJPEG and HIP errors now throw ``std::runtime_error`` instead of
       calling ``exit(1)``
   * - NIfTI big-endian
     - Fixed voxel byte-swap for big-endian NIfTI-1 volumes
   * - Separable filter precision
     - Fixed int64/uint64 min/max separable filter precision loss
   * - Integer interpolation on HIP
     - Fixed undefined-behaviour narrowing in integer interpolation on the HIP
       backend

Known limitations
=================

- OME-TIFF Z/T axis metadata: multi-page TIFFs surface as a flat level list with
  ``dims="YXC"``. Z/T axis population from OME-XML isn't implemented yet
- NIfTI-1 complex64, complex128, and RGB/RGBA voxel types aren't supported.
  Opening such a volume raises ``Unsupported NIfTI datatype``
- DICOM MONOCHROME1 pixel data is returned as stored. The photometric inversion
  isn't applied automatically
- DICOM multi-frame, DICOM-WSI, DICOM-SEG, and DICOM SR aren't supported in
  Phase 1
- JPEG 2000 GPU decode: no ROCm-native JP2K GPU decoder exists. JP2K tiles
  always decode on CPU with OpenJPEG
- Vectra-QPTIFF: 2 of 6 test files fail to open due to a proprietary metadata
  variant
- Non-JPEG tile formats (PNG, LZW, raw) within TIFF are read on CPU
