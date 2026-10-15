#
# cmake-format: off
# SPDX-FileCopyrightText: Copyright (c) 2020-2026, NVIDIA CORPORATION.
# SPDX-License-Identifier: Apache-2.0
#
# Modifications Copyright (C) 2024-2026 Advanced Micro Devices, Inc. All rights reserved.
# cmake-format: on
#

cmake_minimum_required(VERSION 4.0 FATAL_ERROR)
# NOTE(HIP/AMD): make *.cu files HIP lang files
set(CMAKE_USER_MAKE_RULES_OVERRIDE "overrides.cmake")

################################################################################
# Prerequisite statements
################################################################################

# Set VERSION and BUILD
unset(VERSION CACHE)
file(STRINGS ${CMAKE_CURRENT_LIST_DIR}/HIPCIM_VERSION VERSION)
# strip alpha version info
string(REGEX REPLACE "a.*$" "" VERSION ${VERSION})
set(PROJECT_VERSION_BUILD dev)

# Append local cmake module path
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}/cpp/cmake/modules")
project(libcucim VERSION ${VERSION} DESCRIPTION "libcucim" LANGUAGES CXX)

# Resolve the ROCm root (and put its libs on LD_LIBRARY_PATH for HIP try_run
# probes), then load HIP. Defined in CuCIMUtils; included early here as it is
# needed before the HIP language is enabled below.
include(CuCIMUtils)
cucim_require_hip()
enable_language(HIP)
include_directories(${HIP_INCLUDE_DIRS})

################################################################################
# Include utilities
################################################################################
include(SuperBuildUtils)
include(CuCIMUtils)

################################################################################
# Basic setup
################################################################################

# Set default build type
set(DEFAULT_BUILD_TYPE "Release")
if (NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    message(STATUS "Setting build type to '${DEFAULT_BUILD_TYPE}' as none was specified.")
    set(CMAKE_BUILD_TYPE "${DEFAULT_BUILD_TYPE}" CACHE STRING "Choose the type of build." FORCE)
    # Set the possible values of build type for cmake-gui
    set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS "Debug" "Release" "MinSizeRel" "RelWithDebInfo")
endif ()

# Set default output directories
if (NOT CMAKE_ARCHIVE_OUTPUT_DIRECTORY)
    set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/lib")
endif ()
if (NOT CMAKE_LIBRARY_OUTPUT_DIRECTORY)
    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/lib")
endif ()
if (NOT CMAKE_RUNTIME_OUTPUT_DIRECTORY)
    set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/bin")
endif ()

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED YES)

# Include CUDA headers explicitly for VSCode intelli-sense
#include_directories(AFTER SYSTEM ${CMAKE_CUDA_TOOLKIT_INCLUDE_DIRECTORIES})
include_directories(AFTER SYSTEM ${ROCM_PATH}/include)

# Disable visibility to not expose unnecessary symbols
set(CMAKE_CXX_VISIBILITY_PRESET default)
set(CMAKE_VISIBILITY_INLINES_HIDDEN NO)

# Set RPATH so the installed/relocated libraries resolve their ROCm dependencies
# (libamdhip64, librocjpeg, ...) across install layouts:
#   $ORIGIN                         co-located hipCIM libraries
#   $ORIGIN/../../_rocm_sdk_*/lib   sibling ROCm pip wheels (relocatable venv)
#   ${ROCM_PATH}/lib                build-time ROCm root (tarball / same venv)
#   /opt/rocm/lib                   classic system install
if (NOT APPLE)
    set(HIPCIM_RPATH "$ORIGIN;$ORIGIN/../../_rocm_sdk_core/lib;$ORIGIN/../../_rocm_sdk_libraries/lib;$ORIGIN/../../_rocm_sdk_devel/lib;${ROCM_PATH}/lib;/opt/rocm/lib")
    set(CMAKE_INSTALL_RPATH "${HIPCIM_RPATH}")
    set(CMAKE_BUILD_RPATH "${HIPCIM_RPATH}")
endif()

# Set Installation setup
if (NOT CMAKE_INSTALL_PREFIX)
    set(CMAKE_INSTALL_PREFIX ${CMAKE_CURRENT_LIST_DIR}/install) # CACHE PATH "install here" FORCE)
endif ()
include(GNUInstallDirs)
# Force to set CMAKE_INSTALL_LIBDIR to lib as the library can be built with Cent OS ('lib64' is set) and
# /usr/local/lib64 or /usr/local/lib is not part of ld.so.conf* (`cat /etc/ld.so.conf.d/* | grep lib64`)
# https://gitlab.kitware.com/cmake/cmake/-/issues/20565
set(CMAKE_INSTALL_LIBDIR lib)

include(ExternalProject)

################################################################################
# Options
################################################################################

# Code Coverage Option
option(ENABLE_CODE_COVERAGE "Enable code coverage instrumentation" OFF)

if(ENABLE_CODE_COVERAGE)
    message(STATUS "Code coverage enabled")

    # Determine which compiler is being used
    # For hipcc, we need to check the actual compiler path
    set(COVERAGE_CXX_FLAGS "")
    set(COVERAGE_C_FLAGS "")

    # Check C++ compiler
    if(CMAKE_CXX_COMPILER MATCHES "hipcc")
        # hipcc compiles every C++ translation unit for BOTH the host and the
        # amdgcn device. LLVM profile instrumentation has no amdgcn runtime, so
        # an unscoped -fprofile-instr-generate makes the device link fail with
        # undefined __llvm_profile_* / __start___llvm_prf_* symbols. Scope the
        # instrumentation to the host sub-compilation with -Xarch_host; -g stays
        # global (debug info is fine on both host and device).
        set(COVERAGE_CXX_FLAGS "-Xarch_host -fprofile-instr-generate -Xarch_host -fcoverage-mapping -g")
        message(STATUS "Using LLVM coverage flags for C++ (hipcc, host-only instrumentation)")
    elseif(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
        # LLVM/Clang coverage flags for C++ (non-offloading clang)
        set(COVERAGE_CXX_FLAGS "-fprofile-instr-generate -fcoverage-mapping -g")
        message(STATUS "Using LLVM coverage flags for C++ (clang)")
    elseif(CMAKE_CXX_COMPILER_ID MATCHES "GNU")
        # GCC coverage flags for C++
        set(COVERAGE_CXX_FLAGS "-fprofile-arcs -ftest-coverage -g")
        message(STATUS "Using GCC coverage flags for C++")
    endif()

    # Check C compiler separately - it might be different
    if(CMAKE_C_COMPILER MATCHES "hipcc" OR CMAKE_C_COMPILER_ID MATCHES "Clang")
        # LLVM/Clang coverage flags for C
        set(COVERAGE_C_FLAGS "-fprofile-instr-generate -fcoverage-mapping -g")
        message(STATUS "Using LLVM coverage flags for C (hipcc/clang)")
    elseif(CMAKE_C_COMPILER_ID MATCHES "GNU" OR CMAKE_C_COMPILER MATCHES "gcc" OR CMAKE_C_COMPILER MATCHES "cc")
        # GCC coverage flags for C
        set(COVERAGE_C_FLAGS "-fprofile-arcs -ftest-coverage -g")
        message(STATUS "Using GCC coverage flags for C")
    endif()

    # Apply the flags
    if(COVERAGE_CXX_FLAGS)
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${COVERAGE_CXX_FLAGS}")
        set(CMAKE_HIP_FLAGS "${CMAKE_HIP_FLAGS} ${COVERAGE_CXX_FLAGS}")
    endif()

    if(COVERAGE_C_FLAGS)
        set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${COVERAGE_C_FLAGS}")
    endif()

    # Export compile commands for verification
    set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

    message(STATUS "Coverage C++ flags: ${COVERAGE_CXX_FLAGS}")
    message(STATUS "Coverage C flags: ${COVERAGE_C_FLAGS}")
endif()

################################################################################
# Options
################################################################################
option(CUCIM_SUPPORT_GDS "Support cufile library" OFF)
option(CUCIM_STATIC_GDS "Use static cufile library" OFF)
option(CUCIM_SUPPORT_CUDA "Support CUDA" ON)
option(CUCIM_SUPPORT_NVTX "Support NVTX" OFF)

# Setup CXX11 ABI
# : Adds CXX11 ABI definition to the compiler command line for targets in the current directory,
#   whether added before or after this command is invoked, and for the ones in sub-directories added after.
add_definitions(-D_GLIBCXX_USE_CXX11_ABI=0) # TODO: create two library, one with CXX11 ABI and one without it.

################################################################################
# Define basic dependencies
################################################################################
# Include pthread
# (https://cmake.org/cmake/help/v3.18/module/FindThreads.html)
set(CMAKE_THREAD_PREFER_PTHREAD TRUE)
set(THREADS_PREFER_PTHREAD_FLAG TRUE)
find_package(Threads REQUIRED)

################################################################################
# Define dependencies
################################################################################
superbuild_depend(fmt)
#superbuild_depend(boost)
superbuild_depend(abseil)
superbuild_depend(googletest)
superbuild_depend(googlebenchmark)
superbuild_depend(openslide)
superbuild_depend(catch2)
superbuild_depend(cli11)
superbuild_depend(json)
superbuild_depend(libcuckoo)
superbuild_depend(boost-header-only)
superbuild_depend(nvtx3)
superbuild_depend(taskflow)

################################################################################
# Define some names
################################################################################
set(CUCIM_PACKAGE_NAME hipcim) # hipcim

################################################################################
# Add subdirectories
################################################################################
add_subdirectory(cpp)
add_subdirectory(gds)
add_subdirectory(benchmarks)
add_subdirectory(examples/cpp)

################################################################################
# Write CMakeLists.txt for C++ examples
################################################################################

configure_file(${CMAKE_CURRENT_LIST_DIR}/examples/cpp/CMakeLists.txt.examples.release.in
    ${CMAKE_CURRENT_BINARY_DIR}/CMakeLists.txt.examples.release
    @ONLY)

################################################################################
# Install
################################################################################
set(INSTALL_TARGETS
        ${CUCIM_PACKAGE_NAME}
        fmt-header-only
        cucim_benchmarks
        cucim_primitives_benchmarks
	cucim_tests
	tiff_image
        )

install(TARGETS ${INSTALL_TARGETS}
        EXPORT ${CUCIM_PACKAGE_NAME}-targets
        RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
                COMPONENT ${CUCIM_PACKAGE_NAME}_Runtime
        LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
                COMPONENT ${CUCIM_PACKAGE_NAME}_Runtime
                NAMELINK_COMPONENT ${CUCIM_PACKAGE_NAME}_Development
        ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
                COMPONENT ${CUCIM_PACKAGE_NAME}_Development
        )

install(EXPORT ${CUCIM_PACKAGE_NAME}-targets
        FILE
            ${CUCIM_PACKAGE_NAME}-targets.cmake
        NAMESPACE
            ${CUCIM_PACKAGE_NAME}::
        DESTINATION
            ${CMAKE_INSTALL_LIBDIR}/cmake/${CUCIM_PACKAGE_NAME})

# Write package configs
include(CMakePackageConfigHelpers)
configure_package_config_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/cpp/cmake/${CUCIM_PACKAGE_NAME}-config.cmake.in
    ${CMAKE_CURRENT_BINARY_DIR}/cpp/cmake/${CUCIM_PACKAGE_NAME}-config.cmake
    INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/${CUCIM_PACKAGE_NAME}
)
write_basic_package_version_file(
    ${CMAKE_CURRENT_BINARY_DIR}/cpp/cmake/${CUCIM_PACKAGE_NAME}-config-version.cmake
    VERSION ${PROJECT_VERSION}
    COMPATIBILITY AnyNewerVersion
)
install(
    FILES
        ${CMAKE_CURRENT_BINARY_DIR}/cpp/cmake/${CUCIM_PACKAGE_NAME}-config.cmake
        ${CMAKE_CURRENT_BINARY_DIR}/cpp/cmake/${CUCIM_PACKAGE_NAME}-config-version.cmake
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/${CUCIM_PACKAGE_NAME}
)

install(DIRECTORY
            ${CMAKE_CURRENT_SOURCE_DIR}/cpp/include/ # Suffix '/' is necessary to not copy to install/include/include folder.
        DESTINATION
            ${CMAKE_INSTALL_INCLUDEDIR})

# Copy 3rdparty headers
install(DIRECTORY
            ${deps-fmt_SOURCE_DIR}/include/
            #${deps-nvtx3_SOURCE_DIR}/c/include/
	    #${deps-nvtx3_SOURCE_DIR}/cpp/include/ --> There is no cpp folder in nvtx
	    ${CMAKE_CURRENT_SOURCE_DIR}/cpp/include/cucim/3rdparty/
        DESTINATION
            ${CMAKE_INSTALL_INCLUDEDIR}/${CUCIM_PACKAGE_NAME}/3rdparty)

set(CMAKE_EXPORT_PACKAGE_REGISTRY ON)
export(PACKAGE ${CUCIM_PACKAGE_NAME})

#set(CPACK_PACKAGE_NAME "${CUCIM_PACKAGE_NAME}")
#set(CPACK_PACKAGE_VENDOR "nvidia.com")
#set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "cuCIM - GPU-accelerated image processing toolkit")
#set(CPACK_PACKAGE_VERSION "${PROJECT_VERSION}")
#set(CPACK_PACKAGE_VERSION_MAJOR "${PROJECT_VERSION_MAJOR}")
#set(CPACK_PACKAGE_VERSION_MINOR "${PROJECT_VERSION_MINOR}")
#set(CPACK_PACKAGE_VERSION_PATCH "${PROJECT_VERSION_PATCH}")
#set(CPACK_PACKAGE_INSTALL_DIRECTORY "cucim_cpack")  # TODO: update this
#include(CPack)

# Unset cached options needed
unset(CUCIM_STATIC_GDS CACHE)
