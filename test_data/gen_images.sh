#!/bin/bash
# SPDX-FileCopyrightText: Copyright (c) 2021-2025, NVIDIA CORPORATION. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Modifications Copyright (C) 2024-2026 Advanced Micro Devices, Inc. All rights reserved.


SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
TOP="$(git rev-parse --show-toplevel 2> /dev/null || echo "${SCRIPT_DIR}/..")"

[ -z "${TOP}" ] && >&2 echo "Repository root is not available!" && exit 1

DEST_FOLDER=${TOP}/test_data/generated
mkdir -p ${DEST_FOLDER}

generate_image() {
    local recipe="${1:-tiff}"
    local check_file="${2:-}"

    [ -n "${check_file}" ] && [ -f "${DEST_FOLDER}/${check_file}" ] && return

    python3 ${TOP}/python/cucim/tests/util/gen_image.py ${recipe} --dest ${DEST_FOLDER}
}

generate_image tiff::stripe:32x32:16 tiff_stripe_32x32_16.tif
generate_image tiff::stripe:4096x4096:256:deflate tiff_stripe_4096x4096_256.tif

# Synthetic NIfTI/DICOM fixtures for the cumed (MedicalImage) C++ tests. The
# generator has per-file guards and no-ops if nibabel/pydicom are unavailable.
python3 ${TOP}/test_data/gen_medical.py --dest ${DEST_FOLDER}/medical
