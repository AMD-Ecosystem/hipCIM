.. meta::
   :description: Supported image formats, GPU operations, and performance for hipCIM
   :keywords: hipCIM, supported functionality, formats, GPU, ROCm, AMD

.. _supported-features:

***********************************
Supported features 
***********************************

Listed here are the supported image formats, GPU-accelerated operations, and known limitations for hipCIM.

Supported image formats
=======================

hipCIM opens the following image formats through the ``hipcim.kit.hipslide`` and
``hipcim.kit.hipmed`` runtime plugins.

.. list-table::
   :header-rows: 1
   :widths: 22 12 34 12

   * - Format
     - Extension
     - Notes
     - GPU tile decode
   * - Aperio ScanScope Virtual Slide (SVS), single-level JPEG
     - ``.svs``
     - | JPEG-compressed tiles.
       | rocJPEG backend.
     - Yes
   * - Philips TIFF, single-level JPEG
     - ``.tiff``
     - | JPEG-compressed tiles.
       | rocJPEG backend.
     - Yes
   * - OME-TIFF (multi-page, Z/T/channel)
     - ``.tif``, ``.tiff``, ``.ome.tiff``
     - | Flat page list.
       | JPEG tiles GPU-decoded.
       | Non-JPEG tiles CPU-decoded.
     - Partial (JPEG tiles)
   * - Generic multi-page TIFF
     - ``.tif``, ``.tiff``
     - | Flat page list.
       | JPEG tiles GPU-decoded.
     - Partial (JPEG tiles)
   * - Vectra-QPTIFF
     - ``.qptiff``
     - | Most files supported.
       | 2 of 6 test files fail due to a proprietary variant.
     - Partial
   * - NIfTI-1 (uncompressed)
     - ``.nii``
     - | CPU read.
       | All supported NIfTI-1 data types.
     - N/A
   * - NIfTI-1 (gzip compressed)
     - ``.nii.gz``
     - | CPU read.
       | libdeflate decompression.
     - N/A
   * - DICOM (uncompressed, single-frame)
     - ``.dcm``
     - | Explicit/Implicit VR Little-Endian.
       | CPU read.
     - N/A
   * - DICOM (JPEG compressed, single-frame)
     - ``.dcm``
     - Enabled by default (``CUMED_DICOM_COMPRESSED=ON``)
     - N/A

.. note::

   SVS/TIFF decode is handled by the ``hipcim.kit.hipslide`` plugin, which loads
   ``librocjpeg.so.1`` and its amdgpu VA-API driver at startup. If those
   libraries are unavailable the plugin fails to load and SVS/TIFF files can't
   be read at all. hipCIM raises ``Cannot find a plugin to handle '.svs'``. See
   :ref:`rocjpeg-runtime` for how the ROCm 10.0 pip packages provide them.

Image format support is also limited by `rocJPEG chroma subsampling and hardware
capabilities <https://rocm.docs.amd.com/projects/rocJPEG/en/latest/reference/rocjpeg-formats-and-architectures.html>`_.

Unsupported image formats
==========================

- NDPI, VMS, MIRAX, SCN, BIF, VSI, CZI, ZVI from vendors such as Zeiss,
  Hamamatsu, and Leica
- DICOM-WSI pyramid, DICOM-SEG, DICOM SR, multi-frame DICOM
- JPEG 2000 GPU decode. OpenJPEG is CPU-only. No ROCm-native JP2K GPU decoder ships
  in this release.
- Dask and GDS integration
- OME-TIFF Z/T axis metadata. Dims stay ``YXC``. OME-XML Z/T parse is planned.

Image operations
================

Listed here are the GPU-accelerated operations supported by ``cucim.core`` and ``cucim.skimage``.

cucim.core: Image interface
---------------------------

``cucim.core`` covers image read, write, resample, and metadata retrieval.

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Operation
     - GPU accelerated
     - CPU fallback
   * - Image read (``read_region``)
     - Yes (JPEG tiles)
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

cucim.skimage: Image processing
-------------------------------

``cucim.skimage`` groups transform, filter, morphology, restoration, color,
measurement, and exposure operations.

.. list-table::
   :header-rows: 1
   :widths: 22 48 30

   * - Category
     - Supported operations
     - GPU accelerated
   * - Transform
     - resize, rotate, warp (batch / multi-channel optimized)
     - Yes
   * - Filters
     - Gaussian, median, Sobel, Prewitt, Scharr, Laplace, unsharp mask, rank
       filters
     - Yes
   * - Morphology
     - erosion, dilation, opening, closing, skeletonize, binary_erosion,
       binary_dilation, h_maxima, h_minima, local_maxima, local_minima
     - Yes
   * - Restoration
     - rolling_ball (background subtraction)
     - Yes
   * - Segmentation
     - Not currently available (watershed, SLIC)
     - No
   * - Color
     - rgb2gray, rgb2hsv, rgb2lab, and all colour space conversions, plus stain
       separation for H&E and DAB
     - Yes
   * - Measurement
     - label (region labeling)
     - Yes
   * - Exposure
     - histogram operations
     - Limited

Not GPU-accelerated
-------------------

- Affine, similarity, and Euclidean transforms
- Denoising such as TV, bilateral, wavelet, and non-local means
- Exposure operations such as ``equalize_hist``, ``adjust_gamma``, and related
  histogram operations
- Image registration functions. Most lack CPU fallbacks.
- felzenszwalb, quickshift, active contour segmentation
- watershed, SLIC
- marching cubes

Performance
===========

The tables below report representative measurements from internal benchmarks.
They aren't produced by in-repository CI.

Whole-slide read throughput on AMD Instinct MI350X, ROCm 10.0.0, measured with
the batched ``read_region`` API (256 px patches, level 0, ``batch_size=128``,
``num_workers=8``, decode realized to a host array). Values are patches per
second. Speedup is GPU vs. the OpenSlide baseline.

.. list-table::
   :header-rows: 1
   :widths: 28 22 22 22 16

   * - Slide
     - GPU (``device="cuda"``)
     - CPU (``device="cpu"``)
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
   * - Generic-TIFF (CMU-1)
     - 42,866
     - 34,227
     - 1,173
     - 36.6×

Single-tile and small-batch ``read_region`` latency (256 px, MI350X, ROCm
10.0.0), showing the rocJPEG handle-pool impact:

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Metric
     - Before pool
     - With pool
   * - Single 256 px ``read_region`` with ``device="cuda"``
     - 3.76 ms
     - 0.515 ms
   * - 64-tile batch ``read_region`` with ``device="cuda"``, total time
     - 8.36 ms
     - 4.50 ms
   * - CPU reference (single 256 px)
     - 0.18 ms
     - 0.18 ms

Representative ``cucim.skimage`` operator latencies at 2048×2048 on MI350X with
ROCm 10.0.0, in milliseconds: rgb2gray 0.019, rgb2hsv 0.034, rgb2lab 0.166,
gaussian 0.100, median 0.618, sobel 0.129, unsharp_mask 0.227, threshold_otsu
0.473, binary_erosion 0.152, binary_dilation 0.153, resize at half scale 0.120,
rescale at 2× 0.116, rotate 30° 0.320, warp_affine 0.994, label 1.044,
distance_transform_edt 1.056.

For MI300X GPU vs. CPU comparison at large block sizes, see the `hipCIM
introductory blog post
<https://rocm.blogs.amd.com/software-tools-optimization/hipcim-intro/README.html>`_.

Backend differences
-------------------

hipCIM is an AMD ROCm port of cuCIM. It might differ from cuCIM in performance
or numerical behavior. Validate results for mission-critical steps and
`report reproducible issues
<https://github.com/AMD-Ecosystem/hipCIM/issues/new>`_.
