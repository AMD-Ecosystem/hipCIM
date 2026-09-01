.. meta::
   :description: Supported image formats
   :keywords: hipCIM, supportedformats, GPU, ROCm, AMD

.. _supported-features:

***********************************
Supported image formats
***********************************

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
     - Partial for JPEG tiles.
   * - Generic multi-page TIFF
     - ``.tif``, ``.tiff``
     - | Flat page list.
       | JPEG tiles GPU-decoded.
     - Partial for JPEG tiles.
   * - Vectra-QPTIFF
     - ``.qptiff``
     - | Most files supported.
       | 2 of 6 test files fail due to a proprietary variant.
     - Partial.
   * - Uncompressed NIfTI-1
     - ``.nii`` 
     - | CPU read.
       | All supported NIfTI-1 data types.
     - N/A.
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
     - Enabled by default with ``CUMED_DICOM_COMPRESSED=ON``.
     - N/A

The following image formats are not supported:

- NDPI, VMS, MIRAX, SCN, BIF, VSI, CZI, and ZVI from vendors such as Zeiss,
  Hamamatsu, and Leica.
- DICOM-WSI pyramid, DICOM-SEG, DICOM SR, and multi-frame DICOM.
- JPEG 2000 GPU decode. OpenJPEG is CPU-only. No ROCm-native JP2K GPU decoder ships
  in this release.
- Dask and GDS integration.
- OME-TIFF Z and T axis metadata. Dimensions stay ``YXC``. OME-XML Z and T
  parsing is planned.

.. note::

   The ``hipcim.kit.hipslide`` plugin handles SVS and TIFF decoding. It loads
   ``librocjpeg.so.1`` and its amdgpu VA-API driver at startup. If those
   libraries are unavailable, the plugin fails to load and SVS and TIFF files can't
   be read. See :ref:`rocjpeg-runtime` for more information.
