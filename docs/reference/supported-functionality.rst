.. meta::
   :description: The hipCIM library is a robust open-source solution developed to significantly accelerate computer vision and image processing capabilities
   :keywords: AMD-Ecosystem, life sciences, hipCIM installation

.. _supported-features:

***********************************
Supported functionality
***********************************

hipCIM supports the image formats, image operations, and performance characteristics described here.

Supported image formats
=======================

.. list-table::
   :header-rows: 1
   :widths: 26 18 38 18

   * - Format
     - Extension
     - Notes
     - GPU tile decode
   * - Aperio ScanScope Virtual Slide (SVS), single-level JPEG
     - ``.svs``
     - JPEG-compressed tiles; rocJPEG backend
     - ✓
   * - Philips TIFF, single-level JPEG
     - ``.tiff``
     - JPEG-compressed tiles; rocJPEG backend
     - ✓
   * - OME-TIFF (multi-page, Z, T, or channel)
     - ``.tif``, ``.tiff``, ``.ome.tiff``
     - Flat page list; JPEG tiles GPU-decoded; non-JPEG tiles CPU-decoded
     - Partial (JPEG tiles)
   * - Generic multi-page TIFF
     - ``.tif``, ``.tiff``
     - Flat page list; JPEG tiles GPU-decoded
     - Partial (JPEG tiles)
   * - Vectra-QPTIFF
     - ``.qptiff``
     - Most files supported; 2/6 test files fail (proprietary variant)
     - Partial
   * - NIfTI-1 (uncompressed)
     - ``.nii``
     - CPU read; all NIfTI-1 data types supported
     - n/a
   * - NIfTI-1 (gzip compressed)
     - ``.nii.gz``
     - CPU read; libdeflate decompression
     - n/a
   * - DICOM (uncompressed, single-frame)
     - ``.dcm``
     - Explicit or Implicit VR Little-Endian; CPU read
     - n/a
   * - DICOM (JPEG compressed, single-frame)
     - ``.dcm``
     - Enabled by default (``CUMED_DICOM_COMPRESSED=ON``)
     - n/a

.. note::

   SVS and TIFF decode (GPU and CPU fallback) is handled by the ``cuslide``
   plugin, which loads ``librocjpeg.so.1`` and its amdgpu VA-API driver at
   startup. If those libraries are unavailable the plugin fails to load and
   SVS and TIFF files cannot be read at all (``Cannot find a plugin to handle
   '.svs'``). See :ref:`rocjpeg-runtime` for how the ROCm 10.0.0 pip packages
   provide them.

Not supported
-------------------

- NDPI, VMS, MIRAX, SCN, BIF, VSI, CZI, ZVI (Zeiss, Hamamatsu, Leica, and others)
- DICOM-WSI pyramid, DICOM-SEG, DICOM SR, multi-frame DICOM
- JPEG 2000 GPU decode (OpenJPEG CPU-only; HIP port not planned)
- Dask and GDS integration
- OME-TIFF Z and T axis metadata (dims stay ``YXC``; OME-XML Z and T parse planned)

Image operations
==================

``cucim.core`` covers the image interface. ``cucim.skimage`` covers image
processing.

cucim.core: Image interface
-----------------------------

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Operation
     - GPU accelerated
     - CPU fallback
   * - Image read (``read_region``)
     - ✓ (JPEG tiles)
     - ✓
   * - Image write
     - ✓
     - ✓
   * - Resample
     - ✓
     - ✓
   * - Metadata retrieval
     - n/a
     - ✓

cucim.skimage: Image processing
---------------------------------

.. list-table::
   :header-rows: 1
   :widths: 20 55 25

   * - Category
     - Supported operations
     - GPU accelerated
   * - Transform
     - resize, rotate, warp (batch and multi-channel optimized)
     - ✓
   * - Filters
     - Gaussian, median, Sobel, Prewitt, Scharr, Laplace, unsharp mask, rank
       filters
     - ✓
   * - Morphology
     - erosion, dilation, opening, closing, skeletonize, binary_erosion,
       binary_dilation, h_maxima, h_minima, local_maxima, local_minima
     - ✓
   * - Restoration
     - rolling_ball (background subtraction)
     - ✓
   * - Segmentation
     - Not currently available (watershed, SLIC)
     - ✗
   * - Color
     - rgb2gray, rgb2hsv, rgb2lab, and all color space conversions; stain
       separation (H&E, DAB)
     - ✓
   * - Measurement
     - label (region labeling)
     - ✓
   * - Exposure
     - histogram operations
     - Limited

Not GPU-accelerated
---------------------

- Affine, similarity, and Euclidean transforms
- Denoising (TV, bilateral, wavelet, non-local means). ``rolling_ball``
  background subtraction is GPU-accelerated.
- Exposure operations (equalize_hist, adjust_gamma, and others)
- Image registration functions (most lack CPU fallbacks)
- felzenszwalb, quickshift, active contour segmentation
- watershed, SLIC
- marching cubes
