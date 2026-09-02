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

# ROCm release series (MAJOR.MINOR) to pin the [rocm] extra against when it
# cannot be detected. This must track the ROCm *release* (the `rocm` pip package
# version, e.g. 10.0.x), NOT the HIP version (e.g. 7.x).
DEFAULT_ROCM_SERIES = "10.0"

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


def _rocm_release_from_disk():
    """ROCm release ``MAJOR.MINOR`` read from files on disk, or "" if not found.
    Reads files only (no subprocess), so it still works under ``pip`` build
    isolation, where the PATH-based ``rocm-sdk`` console-script probe may not be
    reachable. Two layouts are handled: the pip ROCm SDK, whose release is the
    ``rocm`` package version in its ``*.dist-info`` dir next to ROCM_PATH's
    ``_rocm_sdk_*`` tree; and a classic ``/opt/rocm``, whose release is in
    ``.info/version``. The HIP header is deliberately not used -- it carries the
    HIP version (e.g. 7.x), not the ROCm release (e.g. 10.0).
    """
    for root in (
        os.environ.get("ROCM_PATH"),
        os.environ.get("ROCM_HOME"),
        "/opt/rocm",
    ):
        if not root:
            continue
        root = Path(root)
        # pip ROCm SDK: ROCM_PATH is .../site-packages/_rocm_sdk_devel, so the
        # `rocm` package dist-info sits in the parent site-packages dir.
        for dist in sorted(root.parent.glob("rocm-*.dist-info")):
            match = re.search(r"rocm-(\d+\.\d+)", dist.name)
            if match:
                return match.group(1)
        # Classic /opt/rocm: the release version lives in .info/version.
        try:
            text = (root / ".info" / "version").read_text()
        except OSError:
            continue
        match = re.search(r"(\d+\.\d+)", text)
        if match:
            return match.group(1)
    return ""


def _detect_rocm_series():
    """ROCm release ``MAJOR.MINOR`` this wheel targets, for the ``[rocm]`` extra
    pin. This is the ROCm *release* version (matching the `rocm` pip package,
    e.g. 10.0), not the HIP version. First match wins: HIPCIM_ROCM_SERIES env
    var, the ROCm release read from disk (works under ``pip`` build isolation),
    ``rocm-sdk version`` (pip ROCm), else DEFAULT_ROCM_SERIES.
    """
    for text in (
        os.environ.get("HIPCIM_ROCM_SERIES", ""),
        _rocm_release_from_disk(),
        _run(["rocm-sdk", "version"]),
    ):
        match = re.search(r"(\d+\.\d+)", text)
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
    ``rocm[libraries,devel,device-gfx942,device-gfx950]==10.0.*``.

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
