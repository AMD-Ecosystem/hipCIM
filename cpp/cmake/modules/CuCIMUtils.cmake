#
# cmake-format: off
# SPDX-FileCopyrightText: Copyright (c) 2020-2025, NVIDIA CORPORATION.
# SPDX-License-Identifier: Apache-2.0
#
# Modifications Copyright (C) 2024-2026 Advanced Micro Devices, Inc. All rights reserved.
# cmake-format: on
#

# Store current BUILD_SHARED_LIBS setting in CUCIM_OLD_BUILD_SHARED_LIBS
if(NOT COMMAND cucim_set_build_shared_libs)
    macro(cucim_set_build_shared_libs new_value)
        set(CUCIM_OLD_BUILD_SHARED_LIBS ${BUILD_SHARED_LIBS}})
        if (DEFINED CACHE{BUILD_SHARED_LIBS})
            set(CUCIM_OLD_BUILD_SHARED_LIBS_CACHED TRUE)
        else()
            set(CUCIM_OLD_BUILD_SHARED_LIBS_CACHED FALSE)
        endif()
        set(BUILD_SHARED_LIBS ${new_value} CACHE BOOL "" FORCE)
    endmacro()
endif()

# Restore BUILD_SHARED_LIBS setting from CUCIM_OLD_BUILD_SHARED_LIBS
if(NOT COMMAND cucim_restore_build_shared_libs)
    macro(cucim_restore_build_shared_libs)
        if (CUCIM_OLD_BUILD_SHARED_LIBS_CACHED)
            set(BUILD_SHARED_LIBS ${CUCIM_OLD_BUILD_SHARED_LIBS} CACHE BOOL "" FORCE)
        else()
            unset(BUILD_SHARED_LIBS CACHE)
            set(BUILD_SHARED_LIBS ${CUCIM_OLD_BUILD_SHARED_LIBS})
        endif()
    endmacro()
endif()

# Define CMAKE_CUDA_ARCHITECTURES for the given architecture values
#
# Params:
#   arch_list - architecture value list (e.g., '60;70;75;80;86')
if(NOT COMMAND cucim_define_cuda_architectures)
    function(cucim_define_cuda_architectures arch_list)
        set(arch_string "")
        # Create SASS for all architectures in the list
        foreach(arch IN LISTS arch_list)
            set(arch_string "${arch_string}" "${arch}-real")
        endforeach(arch)

        # Create PTX for the latest architecture for forward-compatibility.
        list(GET arch_list -1 latest_arch)
        foreach(arch IN LISTS arch_list)
            set(arch_string "${arch_string}" "${latest_arch}-virtual")
        endforeach(arch)
        set(CMAKE_CUDA_ARCHITECTURES ${arch_string} PARENT_SCOPE)
    endfunction()
endif()

# Resolve the ROCm root and prepare the environment for HIP builds. Sets
# ${out_var} (caller scope) to the ROCm root, resolved like run_amd's
# init_globals: ROCM_PATH env > ROCM_HOME env > `rocm-sdk path --root` > hipcc
# location > /opt/rocm. Also prepends ${root}/lib to LD_LIBRARY_PATH so
# hipcc-linked try_run probes (e.g. googlebenchmark's regex backend, which links
# libamdhip64.so) can run during configuration.
if(NOT COMMAND cucim_resolve_rocm_path)
    function(cucim_resolve_rocm_path out_var)
        # Treat an empty ROCM_PATH/ROCM_HOME as unset: a defined-but-empty value
        # would otherwise yield an empty root and break include/RPATH entries
        # (e.g. ${ROCM_PATH}/lib). Fall through to rocm-sdk/hipcc/-opt detection.
        if(NOT "$ENV{ROCM_PATH}" STREQUAL "")
            set(_rocm_root "$ENV{ROCM_PATH}")
        elseif(NOT "$ENV{ROCM_HOME}" STREQUAL "")
            set(_rocm_root "$ENV{ROCM_HOME}")
        else()
            find_program(ROCM_SDK_EXECUTABLE rocm-sdk)
            set(_rocm_sdk_root "")
            if(ROCM_SDK_EXECUTABLE)
                execute_process(
                    COMMAND "${ROCM_SDK_EXECUTABLE}" path --root
                    OUTPUT_VARIABLE _rocm_sdk_root
                    RESULT_VARIABLE _rocm_sdk_rc
                    OUTPUT_STRIP_TRAILING_WHITESPACE
                    ERROR_QUIET)
                if(NOT _rocm_sdk_rc EQUAL 0)
                    message(DEBUG "hipCIM: rocm-sdk path --root exited with ${_rocm_sdk_rc}; skipping")
                    set(_rocm_sdk_root "")
                endif()
            endif()
            if(_rocm_sdk_root AND IS_DIRECTORY "${_rocm_sdk_root}")
                set(_rocm_root "${_rocm_sdk_root}")
            else()
                find_program(HIPCC_EXECUTABLE hipcc)
                if(HIPCC_EXECUTABLE)
                    # Resolve symlinks first: distro packages expose
                    # /usr/bin/hipcc -> /etc/alternatives/hipcc ->
                    # /opt/rocm-X.Y.Z/bin/hipcc, so the unresolved path would
                    # yield _rocm_root=/usr and break find_package(HIP).
                    get_filename_component(_hipcc_real "${HIPCC_EXECUTABLE}" REALPATH)
                    get_filename_component(_hipcc_bin "${_hipcc_real}" DIRECTORY)
                    get_filename_component(_rocm_root "${_hipcc_bin}" DIRECTORY)
                else()
                    set(_rocm_root "/opt/rocm")
                endif()
            endif()
            # Ignore an auto-detected root that does not hold a ROCm install.
            # An explicit ROCM_PATH/ROCM_HOME is always honoured as given.
            if(NOT IS_DIRECTORY "${_rocm_root}/lib/cmake/hip" AND NOT EXISTS "${_rocm_root}/bin/hipcc")
                set(_rocm_root "/opt/rocm")
            endif()
        endif()

        # Prepend ${_rocm_root}/lib to LD_LIBRARY_PATH only if not already
        # present, so repeated calls (top-level project + subprojects) do not
        # accumulate duplicate entries.  Note: this mutation is permanent for
        # the CMake process lifetime (needed by hipcc-linked try_run probes).
        set(_rocm_lib "${_rocm_root}/lib")
        if("$ENV{LD_LIBRARY_PATH}" STREQUAL "")
            set(ENV{LD_LIBRARY_PATH} "${_rocm_lib}")
        else()
            string(FIND ":$ENV{LD_LIBRARY_PATH}:" ":${_rocm_lib}:" _rocm_lib_pos)
            if(_rocm_lib_pos EQUAL -1)
                set(ENV{LD_LIBRARY_PATH} "${_rocm_lib}:$ENV{LD_LIBRARY_PATH}")
            endif()
        endif()

        message(STATUS "hipCIM: using ROCM_PATH=${_rocm_root}")
        set(${out_var} "${_rocm_root}" PARENT_SCOPE)
    endfunction()
endif()

# Resolve the ROCm root, make it discoverable by find_package() and load HIP.
# Defined as a macro (not a function) so the HIP_* variables the callers use
# afterwards (HIP_INCLUDE_DIRS, ...) land in the caller's scope.
if(NOT COMMAND cucim_require_hip)
    macro(cucim_require_hip)
        cucim_resolve_rocm_path(ROCM_PATH)
        # Append, never overwrite: a caller-supplied CMAKE_PREFIX_PATH (-D or
        # env) would otherwise hide the HIP package under ${ROCM_PATH}/lib/cmake
        # and make find_package(HIP) fail on non-/opt/rocm installs.
        list(APPEND CMAKE_PREFIX_PATH "${ROCM_PATH}")
        list(REMOVE_DUPLICATES CMAKE_PREFIX_PATH)
        find_package(HIP QUIET)
        if(NOT HIP_FOUND)
            message(FATAL_ERROR
                "hipCIM: the HIP CMake package was not found under '${ROCM_PATH}'.\n"
                "Point ROCM_PATH (or ROCM_HOME) at the ROCm root that contains lib/cmake/hip, "
                "e.g. `export ROCM_PATH=/opt/rocm-7.2.3`, or configure with -DCMAKE_PREFIX_PATH=<rocm-root>.")
        endif()
    endmacro()
endif()
