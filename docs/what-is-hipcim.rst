.. meta::
   :description: hipCIM plugins and capabilities on AMD Instinct GPUs
   :keywords: hipCIM, overview, cuCIM, hipslide, hipmed, AMD Instinct, ROCm

.. _what-is-hipcim:

****************
What is hipCIM?
****************

hipCIM is the AMD ROCm port of `rapidsai/cucim <https://github.com/rapidsai/cucim>`_ for
GPU-accelerated biomedical image I/O and N-dimensional image processing on AMD Instinct GPUs.
The library provides a drop-in replacement API for `cuCIM
<https://docs.rapids.ai/api/cucim/stable/>`_ that lets existing Python code run
unchanged on AMD hardware.

Derived from the `NVIDIA RAPIDS open-source project cuCIM
<https://docs.rapids.ai/api/cucim/stable/>`_, hipCIM maintains the cuCIM API
surface. This lets you transition workloads to AMD devices without
:doc:`hipification <hipify:index>` or changes to your existing codebase.

hipCIM is an open-source library for GPU-accelerated computer vision and image processing. It
targets multidimensional images in biomedical, geospatial, materials, life sciences, and remote
sensing. hipCIM supports GPU-accelerated I/O and N-dimensional processing for digital pathology,
CT, MRI, PET, and related modalities.

Architecture
============

hipCIM exposes a C++ plugin architecture and Python bindings through the ``cucim`` module via
pybind11. Two runtime plugins ship with the library. The ``plugin_version`` placeholder identifies
the plugin version in each file name.

- ``hipcim.kit.hipslide@plugin_version.so`` provides Whole Slide Image, or WSI,
  I/O for SVS, OME-TIFF, multi-page TIFF, and Philips TIFF. rocJPEG provides
  GPU-accelerated JPEG tile decoding. The ``cucim.kit.cuslide`` sources build
  the plugin.

- ``hipcim.kit.hipmed@plugin_version.so`` provides volumetric medical image I/O
  for NIfTI-1 ``.nii`` and ``.nii.gz`` files and single-frame DICOM ``.dcm``
  files. The plugin registers the ``cucim.kit.cumed`` interface. The
  ``cucim.kit.cumed`` sources build the plugin.

``cucim.skimage`` is a CuPy-backed GPU port of scikit-image for image transforms,
filtering, morphology, segmentation, and color operations.

Capabilities
============

hipCIM supports these workloads:

- Efficient image I/O for large images, including whole-slide digital pathology

- N-dimensional image processing for biomedical imaging and related fields

- GPU acceleration for compute-intensive image processing tasks

- Extensible C++ and Python APIs with a plugin mechanism

- Interoperability with other AMD Ecosystem libraries and `CuPy <https://cupy.dev/>`_

- Accelerated patch and tile workflows for high-resolution imaging

hipCIM bridges cuCIM workloads to AMD Instinct GPUs while keeping the same Python API surface.

The hipCIM project is located in `AMD-Ecosystem/hipCIM <https://github.com/AMD-Ecosystem/hipCIM>`_.
