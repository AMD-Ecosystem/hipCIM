#
# SPDX-FileCopyrightText: Copyright (c) 2021, NVIDIA CORPORATION.
# SPDX-License-Identifier: Apache-2.0
#
# Modifications Copyright (C) 2024-2026 Advanced Micro Devices, Inc. All rights reserved.
#

import importlib.util

import pytest

from ...util.io import open_image_cucim

# Only the tests that build a JPEG test image (via the ImageGenerator-backed
# testimg_* fixture) need imagecodecs; guard just those so the fixture-less
# tests still run when imagecodecs is absent.
requires_imagecodecs = pytest.mark.skipif(
    importlib.util.find_spec("imagecodecs") is None,
    reason="imagecodecs not installed (needed to generate the JPEG test image)",
)


def test_load_non_existing_image():
    with pytest.raises(ValueError, match=r"Cannot open .*"):
        _ = open_image_cucim("/tmp/non_existing_image.tif")


@requires_imagecodecs
def test_read_region_save_ppm(testimg_tiff_stripe_32x24_16_jpeg, tmp_path):
    from cucim import CuImage

    img = CuImage(testimg_tiff_stripe_32x24_16_jpeg)
    region = img.read_region((0, 0), (16, 16))

    out_path = tmp_path / "region.ppm"
    region.save(str(out_path))

    data = out_path.read_bytes()
    # CuImage.save() writes a binary (P6) PPM file of the loaded region.
    assert data.startswith(b"P6")
    assert len(data) > 16 * 16 * 3


@requires_imagecodecs
def test_associated_image_missing_returns_empty(
    testimg_tiff_stripe_32x24_16_jpeg,
):
    from cucim import CuImage

    img = CuImage(testimg_tiff_stripe_32x24_16_jpeg)
    # The generated test image has no associated images.
    assert img.associated_images == set()
    # Requesting a non-existent associated image yields an unloaded CuImage.
    assert not img.associated_image("does_not_exist").is_loaded


@requires_imagecodecs
def test_read_region_is_iterable(testimg_tiff_stripe_32x24_16_jpeg):
    from cucim import CuImage

    img = CuImage(testimg_tiff_stripe_32x24_16_jpeg)
    region = img.read_region((0, 0), (16, 16))

    # A non-batched read result is iterable and yields itself once.
    items = list(region)
    assert len(items) == 1

    # Its iterator reports a batch length of 1.
    assert len(iter(region)) == 1


def test_profiler_and_trace_accessors():
    from cucim import CuImage

    # Static accessors on CuImage return a profiler object and a bool flag.
    assert CuImage.profiler() is not None
    assert isinstance(CuImage.is_trace_enabled, bool)

    # The keyword form updates the profiler trace configuration.
    assert CuImage.profiler(trace=True) is not None
    assert CuImage.is_trace_enabled is True
    # Restore the default so the (process-global) trace flag does not leak.
    CuImage.profiler(trace=False)
    assert CuImage.is_trace_enabled is False
