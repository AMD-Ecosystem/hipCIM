.. meta::
   :description: Supported image formats, GPU operations, and performance for hipCIM
   :keywords: hipCIM, supported functionality, formats, GPU, ROCm, AMD

.. _supported-features:

***********************************
Supported features
***********************************

hipCIM supports multiple biomedical image formats and GPU-accelerated
operations. Known limitations identify unsupported formats and operations.

Supported image formats
=======================

The ``hipcim.kit.hipslide`` and ``hipcim.kit.hipmed`` runtime plugins open the
supported image formats.

.. list-table::
   :header-rows: 1
   :widths: 22 12 34 12

   * - Format
     - Extension
     - Notes
     - GPU tile decode
   * - Aperio ScanScope Virtual Slide, or SVS, with single-level JPEG
     - ``.svs``
     - | JPEG-compressed tiles.
       | rocJPEG backend.
     - Yes
   * - Philips TIFF, single-level JPEG
     - ``.tiff``
     - | JPEG-compressed tiles.
       | rocJPEG backend.
     - Yes
   * - Multi-page OME-TIFF with Z, T, or channel data
     - ``.tif``, ``.tiff``, ``.ome.tiff``
     - | Flat page list.
       | JPEG tiles GPU-decoded.
       | Non-JPEG tiles CPU-decoded.
     - Partial for JPEG tiles
   * - Generic multi-page TIFF
     - ``.tif``, ``.tiff``
     - | Flat page list.
       | JPEG tiles GPU-decoded.
     - Partial for JPEG tiles
   * - Vectra-QPTIFF
     - ``.qptiff``
     - | Most files supported.
       | 2 of 6 test files fail due to a proprietary variant.
     - Partial
   * - Uncompressed NIfTI-1
     - ``.nii``
     - | CPU read.
       | All supported NIfTI-1 data types.
     - N/A
   * - Gzip-compressed NIfTI-1
     - ``.nii.gz``
     - | CPU read.
       | libdeflate decompression.
     - N/A
   * - Uncompressed single-frame DICOM
     - ``.dcm``
     - | Explicit or Implicit VR Little-Endian.
       | CPU read.
     - N/A
   * - JPEG-compressed single-frame DICOM
     - ``.dcm``
     - Enabled by default with ``CUMED_DICOM_COMPRESSED=ON``
     - N/A

.. note::

   The ``hipcim.kit.hipslide`` plugin handles SVS and TIFF decoding. It loads
   ``librocjpeg.so.1`` and its amdgpu VA-API driver at startup. If those
   libraries are unavailable, the plugin fails to load and SVS and TIFF files can't
   be read at all. hipCIM raises ``Cannot find a plugin to handle '.svs'``. See
   :ref:`rocjpeg-runtime` for how the ROCm 10.0 pip packages provide them.

Image format support is also limited by `rocJPEG chroma subsampling and hardware
capabilities <https://rocm.docs.amd.com/projects/rocJPEG/en/latest/reference/rocjpeg-formats-and-architectures.html>`_.

Unsupported image formats
==========================

- NDPI, VMS, MIRAX, SCN, BIF, VSI, CZI, and ZVI from vendors such as Zeiss,
  Hamamatsu, and Leica
- DICOM-WSI pyramid, DICOM-SEG, DICOM SR, and multi-frame DICOM
- JPEG 2000 GPU decode. OpenJPEG is CPU-only. No ROCm-native JP2K GPU decoder ships
  in this release.
- Dask and GDS integration
- OME-TIFF Z and T axis metadata. Dimensions stay ``YXC``. OME-XML Z and T
  parsing is planned.

Image operations
================

``cucim.core`` and ``cucim.skimage`` provide GPU-accelerated image operations.

``cucim.core`` image interface
--------------------------------

``cucim.core`` covers image read, write, resample, and metadata retrieval.

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Operation
     - GPU accelerated
     - CPU fallback
   * - Image read with ``read_region()``
     - Yes for JPEG tiles
     - Yes
   * - Image write
     - Yes
     - Yes
   * - Resample
     - Yes
     - Yes
   * - Metadata retrieval
     - N/A
     - Yes

``cucim.skimage`` image processing
------------------------------------

``cucim.skimage`` groups transform, filter, morphology, restoration, color,
measurement, and exposure operations.

.. list-table::
   :header-rows: 1
   :widths: 22 48 30

   * - Category
     - Supported operations
     - GPU accelerated
   * - Transform
     - ``resize()``, ``rotate()``, and ``warp()`` with batch and multi-channel
       optimizations
     - Yes
   * - Filters
     - ``gaussian()``, ``median()``, ``sobel()``, ``prewitt()``, ``scharr()``,
       ``laplace()``, ``unsharp_mask()``, and rank filters
     - Yes
   * - Morphology
     - ``erosion()``, ``dilation()``, ``opening()``, ``closing()``,
       ``skeletonize()``, ``binary_erosion()``, ``binary_dilation()``,
       ``h_maxima()``, ``h_minima()``, ``local_maxima()``, and
       ``local_minima()``
     - Yes
   * - Restoration
     - ``rolling_ball()`` for background subtraction
     - Yes
   * - Segmentation
     - Not currently available for watershed and SLIC
     - No
   * - Color
     - ``rgb2gray()``, ``rgb2hsv()``, ``rgb2lab()``, color space conversions,
       and stain separation for H&E and DAB
     - Yes
   * - Measurement
     - ``label()`` for region labeling
     - Yes
   * - Exposure
     - histogram operations
     - Limited

Not GPU-accelerated
-------------------

- Affine, similarity, and Euclidean transforms.
- Denoising such as TV, bilateral, wavelet, and non-local means.
- Exposure operations such as ``equalize_hist()``, ``adjust_gamma()``, and
  related histogram operations.
- Most image registration functions lack CPU fallbacks.
- Felzenszwalb, quickshift, and active contour segmentation.
- Watershed and SLIC.
- Marching cubes.

Performance
===========

The tables report representative measurements from internal benchmarks.
They aren't produced by in-repository CI.

The whole-slide read throughput benchmark uses AMD Instinct MI350X with ROCm
10.0.0. The batched ``read_region()`` API uses 256 px patches at level 0,
``batch_size=128``, and ``num_workers=8``. The benchmark realizes decoded data
to a host array. Values are patches per second. Speedup compares the GPU with
the OpenSlide baseline.

.. list-table::
   :header-rows: 1
   :widths: 28 22 22 22 16

   * - Slide
     - GPU with ``device="cuda"``
     - CPU with ``device="cpu"``
     - OpenSlide baseline
     - GPU speedup
   * - CMU-1.svs
     - 39,864
     - 29,350
     - 1,217
     - 32.8×
   * - CMU-2.svs
     - 42,937
     - 27,549
     - 1,234
     - 34.8×
   * - CMU-3.svs
     - 42,152
     - 29,369
     - 1,232
     - 34.2×
   * - Generic-TIFF, CMU-1
     - 42,866
     - 34,227
     - 1,173
     - 36.6×

Single-tile and small-batch ``read_region()`` latency uses 256 px tiles on
MI350X with ROCm 10.0.0. The results show the rocJPEG handle-pool impact.

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Metric
     - Before pool
     - With pool
   * - Single 256 px ``read_region()`` with ``device="cuda"``
     - 3.76 ms
     - 0.515 ms
   * - 64-tile batch ``read_region()`` with ``device="cuda"``, total time
     - 8.36 ms
     - 4.50 ms
   * - CPU reference, single 256 px
     - 0.18 ms
     - 0.18 ms

Representative ``cucim.skimage`` operator latencies use 2048×2048 images on
MI350X with ROCm 10.0.0. Each value is in milliseconds.
``rgb2gray()`` 0.019, ``rgb2hsv()`` 0.034, ``rgb2lab()`` 0.166,
``gaussian()`` 0.100, ``median()`` 0.618, ``sobel()`` 0.129,
``unsharp_mask()`` 0.227, ``threshold_otsu()`` 0.473, ``binary_erosion()``
0.152, ``binary_dilation()`` 0.153, ``resize()`` at half scale 0.120,
``rescale()`` at 2× 0.116, ``rotate()`` at 30° 0.320, ``warp_affine()`` 0.994,
``label()`` 1.044, and ``distance_transform_edt()`` 1.056.

For MI300X GPU vs. CPU comparison at large block sizes, see the `hipCIM
introductory blog post
<https://rocm.blogs.amd.com/software-tools-optimization/hipcim-intro/README.html>`_.

Backend differences
-------------------

hipCIM is an AMD ROCm port of cuCIM. It might differ from cuCIM in performance
or numerical behavior. Validate results for mission-critical steps and
`report reproducible issues
<https://github.com/AMD-Ecosystem/hipCIM/issues/new>`_.
