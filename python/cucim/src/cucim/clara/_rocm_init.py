# SPDX-FileCopyrightText: Copyright (C) 2024-2026 Advanced Micro Devices, Inc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""Preload ROCm shared libraries via the ROCm (TheRock) Python packages.

When hipCIM is installed as a wheel alongside the ROCm Python packages
(``pip install "rocm[libraries]"``), the ROCm runtime libraries live inside the
``_rocm_sdk_*`` trees in ``site-packages`` rather than on the default dynamic
loader search path. Asking ``rocm_sdk`` to load them into the global symbol
namespace lets hipCIM's own native extensions resolve their ROCm dependencies
(``libamdhip64``, ``librocjpeg``, ...) regardless of the wheel's install
location or the active virtual environment.

This is a best-effort no-op when the ``rocm_sdk`` package is not installed --
for example when ROCm is provided by a classic system ``/opt/rocm`` install that
is instead picked up through the libraries' RPATH.

This module also points libva at ROCm's VA-API driver, which rocJPEG needs for
GPU decode. See ``_configure_vaapi`` for why that cannot be left to the loader.
"""

import os
from pathlib import Path

# Short (SONAME-less) names of the ROCm libraries that hipCIM's native
# extensions link against directly. Their own transitive dependencies
# (hsa-runtime64, amd_comgr, hiprtc, ...) are resolved by the ROCm packages'
# RPATHs once these are loaded.
_PRELOAD_SHORTNAMES = [
    "amdhip64",
    "rocjpeg",
]

# libva builds its backend filename as "<name>_drv_video.so". The name comes
# from LIBVA_DRIVER_NAME, or from libva's own kernel-driver map, which pairs the
# amdgpu DRM driver with radeonsi. ROCm's vendored Mesa build answers to both
# names; the distribution's driver of the same name is not interchangeable.
_VA_DRIVER_NAMES = ("radeonsi", "amdgpu")


def _va_driver_dirs():
    """Directories that may hold ROCm's VA-API driver, most specific first."""
    for var in ("ROCM_PATH", "ROCM_HOME"):
        root = os.environ.get(var)
        if root:
            yield Path(root, "lib", "rocm_sysdeps", "lib")

    try:
        import rocm_sdk

        for lib in rocm_sdk.find_libraries("rocjpeg"):
            # lib is <site-packages>/_rocm_sdk_<component>/lib/librocjpeg.so.N;
            # the driver may live in any of the sibling component trees.
            site_packages = lib.parent.parent.parent
            yield from sorted(
                site_packages.glob("_rocm_sdk_*/lib/rocm_sysdeps/lib")
            )
    except Exception:
        pass

    # System installs: /opt/rocm is a symlink farm over /opt/rocm/core-<version>
    # in newer packages, and the versioned directory alone in an apt install.
    yield Path("/opt/rocm/lib/rocm_sysdeps/lib")
    yield from sorted(Path("/opt/rocm").glob("core-*/lib/rocm_sysdeps/lib"))


def _configure_vaapi() -> None:
    """Point libva at ROCm's VA-API driver unless the caller chose one.

    libva does not find its backend through the dynamic loader: it dlopens
    ``<driver>_drv_video.so`` from a directory fixed when libva was built, which
    ``LD_LIBRARY_PATH`` does not influence. ROCm vendors libva 1.22 and ships
    the only matching driver inside its own tree, so without this the
    distribution driver (built against VA-API 1.20) is rejected and rocJPEG
    fails with ``ROCJPEG_STATUS_NOT_INITIALIZED``.
    """
    if os.environ.get("LIBVA_DRIVERS_PATH"):
        return

    requested = os.environ.get("LIBVA_DRIVER_NAME")
    names = (requested,) if requested else _VA_DRIVER_NAMES
    fallback = None

    for directory in _va_driver_dirs():
        for name in names:
            if (directory / f"{name}_drv_video.so").is_file():
                os.environ["LIBVA_DRIVERS_PATH"] = str(directory)
                return
        if fallback is None and not requested:
            # Runtime-only ROCm wheels ship the Mesa backend under its mangled
            # SONAME (librocm_sysdeps_gallium_drv_video.so) and omit the
            # radeonsi symlink, so name the file libva should load explicitly.
            for driver in sorted(directory.glob("*_drv_video.so")):
                fallback = (directory, driver.name[: -len("_drv_video.so")])
                break

    if fallback is not None:
        directory, name = fallback
        os.environ["LIBVA_DRIVERS_PATH"] = str(directory)
        os.environ["LIBVA_DRIVER_NAME"] = name


def initialize() -> None:
    """Preload ROCm libraries if the ROCm Python packages are available."""
    _configure_vaapi()

    try:
        import rocm_sdk
    except ModuleNotFoundError:
        return

    try:
        rocm_sdk.initialize_process(preload_shortnames=_PRELOAD_SHORTNAMES)
    except Exception:
        # Best effort: fall back to RPATH / LD_LIBRARY_PATH based resolution.
        pass
