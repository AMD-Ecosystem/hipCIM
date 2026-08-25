.. meta::
   :description: hipCIM plugins and capabilities on AMD Instinct GPUs
   :keywords: hipCIM, overview, cuCIM, hipslide, hipmed, AMD Instinct, ROCm

.. _what-is-hipcim:

****************
What is hipCIM?
****************

hipCIM is the AMD/ROCm port of `rapidsai/cucim <https://github.com/rapidsai/cucim>`_ for
GPU-accelerated biomedical image I/O and N-dimensional image processing on AMD Instinct GPUs.
The library provides a drop-in replacement API for `cuCIM
<https://docs.rapids.ai/api/cucim/stable/>`_, allowing existing Python code to
run unchanged on AMD hardware.

Derived from the `NVIDIA RAPIDS open-source project cuCIM
<https://docs.rapids.ai/api/cucim/stable/>`_, hipCIM maintains full API compatibility with the
cuCIM library. This lets you transition workloads to AMD devices without :doc:`hipification
<hipify:index>` or changes to your existing codebase.

hipCIM is an open-source library for GPU-accelerated computer vision and image processing. It
targets multidimensional images in biomedical, geospatial, materials and life sciences, and remote
sensing. hipCIM supports GPU-accelerated I/O and N-dimensional processing for digital pathology,
CT, MRI, PET, and related modalities.

Architecture
============

hipCIM exposes a C++ plugin architecture and Python bindings through the ``cucim`` module via
pybind11. Two runtime plugins ship with the library:

- ``hipcim.kit.hipslide@<version>.so``: Whole Slide Image, or WSI, I/O for SVS,
  OME-TIFF, multi-page TIFF, and Philips TIFF, with GPU-accelerated JPEG tile
  decode via rocJPEG. Built from the ``cucim.kit.cuslide`` sources.

- ``hipcim.kit.hipmed@<version>.so``: Volumetric medical image I/O for NIfTI-1
  ``.nii``/``.nii.gz`` and single-frame DICOM ``.dcm``. Registers the
  ``cucim.kit.cumed`` interface. Built from the ``cucim.kit.cumed`` sources.

``cucim.skimage`` is a CuPy-backed GPU port of scikit-image for image transforms,
filtering, morphology, segmentation, and colour operations.

Capabilities
============

hipCIM supports the following workloads:

- Efficient image I/O for large images, including whole-slide digital pathology

- N-dimensional image processing for biomedical imaging and related fields

- GPU acceleration for compute-intensive image processing tasks

- Extensible C++ and Python APIs with a plugin mechanism

- Interoperability with other AMD Ecosystem libraries and `CuPy <https://cupy.dev/>`_

- Accelerated patch and tile workflows for high-resolution imaging

hipCIM bridges cuCIM workloads to AMD Instinct GPUs while keeping the same Python API surface.

The hipCIM project is located in `AMD-Ecosystem/hipCIM <https://github.com/AMD-Ecosystem/hipCIM>`_.
