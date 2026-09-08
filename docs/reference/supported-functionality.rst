.. meta::
   :description: The hipCIM library is a robust open-source solution developed to significantly accelerate computer vision and image processing capabilities
   :keywords: ROCm-LS, life sciences, hipCIM installation

.. _supported-features:

***********************************
Supported features and limitations
***********************************

This topic discusses the supported features and limitations of hipCIM 26.06.00 as compared to the `cuCIM 26.06.00 <https://github.com/rapidsai/cucim/releases#release-v26.06.00>`_.

Features
---------

- **Core image interface (cucim.core):**

  - All primary image manipulation functions (read, write, and resample) are GPU-accelerated with CPU fallbacks.

  - Metadata operations (accessing dtype, dims, and shape) run on CPU only.

- **Image processing (cucim.skimage):**

  - Nearly all transform operations (resize, rotate, and warp) are GPU-accelerated with CPU fallbacks.

  - Complete filter suite (Gaussian, median, and edge detectors) benefits from GPU acceleration.

  - Most morphological operations (erosion, dilation, and opening) are GPU-accelerated.

- **Segmentation:**

  - Several advanced segmentation algorithms (felzenszwalb, quickshift, and active_contour) lack GPU acceleration.

  - Core segmentation operations such as watershed and SLIC are GPU-accelerated.

- **Color operations:**

  - All color space conversions (rgb2gray, rgb2hsv, and rgb2lab) are GPU-accelerated.

  - Specialized medical imaging operations, such as stain separation or combination, that also benefit from GPU acceleration.

- **Whole slide imaging:**

  - Patch extraction operations are GPU-accelerated.

  - Metadata operations run exclusively on the CPU.

- **Measurement functions:**

  - Core measurement functions such as region labeling are GPU-accelerated.

  - Some advanced functions such as ``marching_cubes`` lack GPU acceleration.

Image support
--------------

hipCIM supports the following image formats:

- Single-level Aperio ScanScope Virtual Slide (SVS) with JPEG compression

- Single-level Philips TIFF with JPEG compression

Note that the image support is limited by `rocJPEG chroma subsampling and hardware capabilities <https://rocm.docs.amd.com/projects/rocJPEG/en/latest/reference/rocjpeg-formats-and-architectures.html>`_.

hipCIM API mirrors `scikit-image <https://scikit-image.org/>`_ for image manipulation and `OpenSlide <https://openslide.org/>`_ for image loading.

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
