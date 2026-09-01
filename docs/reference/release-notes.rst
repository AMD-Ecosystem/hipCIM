.. meta::
   :description: New features in hipCIM 26.06.00
   :keywords: hipCIM, release notes, hipCIM 26.06.00, ROCm, AMD

.. _whats-new:

**********************************
Release notes for hipCIM 26.06.00
**********************************

hipCIM 26.06.00 is based on upstream cuCIM 26.06.00. This release adds medical
imaging readers, multi-format TIFF support, and rocJPEG performance improvements.

New features
============

hipCIM 26.06.00 adds image format support, decoding improvements, and new image
processing operations.

OME-TIFF and multi-page TIFF support
-------------------------------------

Prior releases rejected any TIFF file with more than one full-resolution IFD
with ``more than one image with Subfile Type 0``. That blocked the OME-TIFF format
family: Z-stacks, time-series, channel-split files, and high-content screening
plates.

hipCIM 26.06.00 removes this restriction. Multi-IFD TIFFs open as a flat page
list, with each Subfile-Type-0 IFD exposed as a level.

.. note::

   This release exposes multi-IFD files as a flat level list with ``dims="YXC"``.
   True Z and T axis support from OME-XML metadata and SubIFD pyramid traversal
   are planned for a future release.


rocJPEG handle pool
-------------------

The process-level ``RocJpegHandlePool`` singleton manages rocJPEG decode
handles. Previously, every ``read_region()`` call created a handle with
``rocJpegCreate()`` and destroyed it with ``rocJpegDestroy()``. Pooling reuses
handles across calls. The benefit is largest for single and small reads.
Batched reads share one handle across the whole batch and see a more modest
gain.

Process-level GPU tile cache
----------------------------

Decoded tiles are cached in a process-level LRU cache keyed on IFD location. On
overlapping or repeated patch reads, tiles can return from the cache without
re-decoding. 

Portable manylinux wheels
-------------------------

Prebuilt ``amd-hipcim`` wheels target the ``manylinux_2_28`` standard and glibc
2.28. ``auditwheel`` repairs the wheels. They run on Linux distributions with
glibc 2.28 or later.

Graceful plugin degradation
---------------------------

When a plugin fails to load at runtime because ``librocjpeg.so.1`` isn't
installed, hipCIM logs a warning and continues with the remaining plugins. NIfTI and DICOM reads can succeed even on hosts where GPU
slide-format libraries are absent.

Resolved issues
===============

This release resolves issues in rocJPEG decoding, medical imaging, and image
processing.

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
     - Fixed ``int64`` and ``uint64`` minimum and maximum separable filter
       precision loss
   * - Integer interpolation on HIP
     - Fixed undefined-behavior narrowing in integer interpolation on the HIP
       backend

