# SPDX-FileCopyrightText: Copyright (c) 2023, NVIDIA CORPORATION.
# SPDX-License-Identifier: Apache-2.0
#
# Modifications Copyright (C) 2024-2026 Advanced Micro Devices, Inc. All rights reserved.
# See file LICENSE for terms.

import os
import re
import subprocess
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    import tomli as tomllib

from setuptools import setup
from setuptools.dist import Distribution as _Distribution

# ROCm series to pin the [rocm] extra against when it cannot be detected.
DEFAULT_ROCM_SERIES = "7.14"

# AMD GPU architectures for the [rocm] device extras when GPU targets are unset.
DEFAULT_GPU_ARCHS = ("gfx942", "gfx950")

_HERE = Path(__file__).parent


def _run(cmd):
    """stdout of ``cmd``, or "" if it is missing or fails."""
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, check=False
        ).stdout
    except OSError:
        return ""


def _hip_version_from_headers():
    """HIP ``MAJOR.MINOR`` parsed from ``hip_version.h`` on disk, or "" if it is
    not found. This reads a file (no subprocess), so it still works under ``pip``
    build isolation, where the PATH-based ``hipcc`` / ``rocm-sdk`` console-script
    probes are not reachable. Looks under ROCM_PATH, ROCM_HOME and ``/opt/rocm``.
    """
    for root in (
        os.environ.get("ROCM_PATH"),
        os.environ.get("ROCM_HOME"),
        "/opt/rocm",
    ):
        if not root:
            continue
        try:
            text = (Path(root) / "include" / "hip" / "hip_version.h").read_text()
        except OSError:
            continue
        major = re.search(r"#define\s+HIP_VERSION_MAJOR\s+(\d+)", text)
        minor = re.search(r"#define\s+HIP_VERSION_MINOR\s+(\d+)", text)
        if major and minor:
            return f"{major.group(1)}.{minor.group(1)}"
    return ""


def _detect_rocm_series():
    """ROCm MAJOR.MINOR this wheel targets, for the ``[rocm]`` extra pin. First
    match wins: HIPCIM_ROCM_SERIES env var, HIP version from ``hip_version.h``
    (works under ``pip`` build isolation), ``hipcc`` HIP version, ``rocm-sdk
    version`` (pip ROCm), else DEFAULT_ROCM_SERIES.
    """
    for text, pattern in (
        (os.environ.get("HIPCIM_ROCM_SERIES", ""), r"(\d+\.\d+)"),
        (_hip_version_from_headers(), r"(\d+\.\d+)"),
        (_run(["hipcc", "--version"]), r"HIP version:\s*(\d+\.\d+)"),
        (_run(["rocm-sdk", "version"]), r"(\d+\.\d+)"),
    ):
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return DEFAULT_ROCM_SERIES


def _detect_gpu_archs():
    """AMD GPU architectures this wheel targets, for the ``rocm[device-gfx*]``
    extras. Reads GPU_TARGETS / AMDGPU_TARGETS (CMake-style list, e.g.
    ``gfx942;gfx950``; also tolerates ``,``/space separators and
    ``gfx942:xnack-`` feature suffixes); falls back to DEFAULT_GPU_ARCHS.
    """
    raw = os.environ.get("GPU_TARGETS") or os.environ.get("AMDGPU_TARGETS", "")
    archs = []
    for match in re.findall(r"gfx[0-9a-f]+", raw, re.IGNORECASE):
        arch = match.lower()
        if arch not in archs:
            archs.append(arch)
    return archs or list(DEFAULT_GPU_ARCHS)


def _rocm_requirement():
    """The ``rocm`` SDK requirement for the [rocm] extra: the runtime libraries,
    the development tools, plus a device extra per targeted GPU arch, pinned to
    the built ROCm series, e.g.
    ``rocm[libraries,devel,device-gfx942,device-gfx950]==7.14.*``.

    ``devel`` is required because amd-cupy JIT-compiles HIP kernels at runtime via
    ``hipcc``; without the ROCm development tree the first GPU operation fails with
    ``clang++: not found``.
    """
    features = ["libraries", "devel"] + [
        f"device-{arch}" for arch in _detect_gpu_archs()
    ]
    return f"rocm[{','.join(features)}]=={_detect_rocm_series()}.*"


def _static_extras():
    """Non-rocm extras, from [tool.hipcim.optional-dependencies]."""
    with open(_HERE / "pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    tool = data.get("tool", {}).get("hipcim", {})
    return dict(tool.get("optional-dependencies", {}))


# optional-dependencies is dynamic (see pyproject.toml) so the `rocm` pin can
# track the ROCm series and GPU archs this wheel is built against. Load the
# static extras and add only `rocm`; override the detected series with
# HIPCIM_ROCM_SERIES and the archs with GPU_TARGETS / AMDGPU_TARGETS.
EXTRAS_REQUIRE = _static_extras()
EXTRAS_REQUIRE["rocm"] = [_rocm_requirement()]


# As we vendored a shared object that links to a specific Python version,
# make sure it is treated as impure so the wheel is named properly.
class Distribution(_Distribution):
    def has_ext_modules(self):
        return True


setup(
    distclass=Distribution,
    extras_require=EXTRAS_REQUIRE,
)
