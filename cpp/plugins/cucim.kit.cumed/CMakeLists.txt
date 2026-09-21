# cmake-format: off
# SPDX-FileCopyrightText: Copyright (c) 2021-2026, NVIDIA CORPORATION
# SPDX-License-Identifier: Apache-2.0
#
# Modifications Copyright (C) 2024-2026 Advanced Micro Devices, Inc. All rights reserved.
# cmake-format: on

cmake_minimum_required(VERSION 4.0 FATAL_ERROR)

################################################################################
# Prerequisite statements
################################################################################

# Set VERSION
unset(VERSION CACHE)
file(STRINGS ${CMAKE_CURRENT_LIST_DIR}/../../../HIPCIM_VERSION VERSION)
# strip alpha version info
string(REGEX REPLACE "a.*$" "" VERSION ${VERSION})

# Append local cmake module path (for SuperBuildUtils.cmake)
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}/cmake/modules")
# Include central CuCIM cmake modules (for CuCIMUtils.cmake)
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}/../../../cpp/cmake/modules")

project(hipmed VERSION ${VERSION} DESCRIPTION "hipmed" LANGUAGES C CXX)
set(CUCIM_PLUGIN_NAME "hipcim.kit.hipmed")

################################################################################
# Include utilities
################################################################################
include(SuperBuildUtils)
include(CuCIMUtils)

################################################################################
# Set cmake policy
################################################################################
if(${CMAKE_VERSION} VERSION_GREATER_EQUAL "3.19")
    cmake_policy(SET CMP0110 NEW) # For add_test() to support arbitrary characters in test name
endif()

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
endif()
if (NOT CMAKE_LIBRARY_OUTPUT_DIRECTORY)
    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/lib")
endif()
if (NOT CMAKE_RUNTIME_OUTPUT_DIRECTORY)
    set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/bin")
endif()

# Find CUDAToolkit
#find_package(CUDAToolkit REQUIRED)
# Resolve the ROCm root (and put its libs on LD_LIBRARY_PATH for HIP try_run
# probes), then load HIP. cucim_require_hip is defined in CuCIMUtils (included
# above) and also sets ROCM_PATH, used further below.
cucim_require_hip()
# For Threads::Threads
find_package(Threads REQUIRED)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED YES)

# Include CUDA headers explicitly for VSCode intelli-sense
#include_directories(AFTER SYSTEM ${CMAKE_CUDA_TOOLKIT_INCLUDE_DIRECTORIES})
include_directories(AFTER SYSTEM ${HIP_INCLUDE_DIRECTORIES})

# Disable visibility to not expose unnecessary symbols
set(CMAKE_CXX_VISIBILITY_PRESET hidden)
set(CMAKE_VISIBILITY_INLINES_HIDDEN YES)

# Set RPATH so libraries resolve their ROCm dependencies across install layouts
# (pip/venv wheels via $ORIGIN, build-time ROCm root, and system /opt/rocm).
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

# Setup CXX11 ABI
# : Adds CXX11 ABI definition to the compiler command line for targets in the current directory,
#   whether added before or after this command is invoked, and for the ones in sub-directories added after.
add_definitions(-D_GLIBCXX_USE_CXX11_ABI=0) # TODO: create two library, one with CXX11 ABI and one without it.

################################################################################
# Define dependencies
################################################################################
superbuild_depend(fmt)
superbuild_depend(catch2)
superbuild_depend(googletest)
superbuild_depend(googlebenchmark)
superbuild_depend(cli11)
superbuild_depend(libdeflate)
# DICOM compressed-pixel decoders — ON by default.
# libjpeg_turbo.cpp and libopenjpeg.cpp are pure CPU code; they do not contain
# HIP/CUDA kernels but are compiled by hipcc (the project CXX compiler). CPATH
# in the CK build environment exposes GCC x86 MMX/SSE intrinsic headers, which
# hipcc/clang rejects with "unknown builtin __builtin_ia32_vec_init_v2si".
# We suppress those macro guards per-file via set_source_files_properties below.
option(CUMED_DICOM_COMPRESSED "Build DICOM JPEG/JP2K decode support (requires cuslide sources)" ON)
if(CUMED_DICOM_COMPRESSED)
    superbuild_depend(libjpeg-turbo)
    superbuild_depend(libopenjpeg)
endif()

################################################################################
# Find cucim package
################################################################################
if (NOT CUCIM_SDK_PATH)
    get_filename_component(CUCIM_SDK_PATH "${CMAKE_SOURCE_DIR}/../../.." ABSOLUTE)
    message("CUCIM_SDK_PATH is not set. Using '${CUCIM_SDK_PATH}'")
else()
    message("CUCIM_SDK_PATH is set to ${CUCIM_SDK_PATH}")
endif()

find_package(hipcim CONFIG REQUIRED
    HINTS ${CUCIM_SDK_PATH}/install/${CMAKE_INSTALL_LIBDIR}/cmake/hipcim
          $ENV{PREFIX}/include/cmake/hipcim # In case conda build is used
    )


################################################################################
# Define compile options
################################################################################

if(NOT BUILD_SHARED_LIBS)
    set(BUILD_SHARED_LIBS ON)
endif()

################################################################################
# Add library: cucim
################################################################################

# Add library
set(CUSLIDE_SRC ${CMAKE_CURRENT_SOURCE_DIR}/../cucim.kit.cuslide/src)
set(CUMED_SRCS
    src/cumed/cumed.cpp
    src/cumed/cumed.h
    src/cumed/nifti.h
    src/cumed/dicom.h
)
if(CUMED_DICOM_COMPRESSED)
    list(APPEND CUMED_SRCS
        ${CUSLIDE_SRC}/cuslide/jpeg/libjpeg_turbo.cpp
        ${CUSLIDE_SRC}/cuslide/jpeg2k/libopenjpeg.cpp
        ${CUSLIDE_SRC}/cuslide/jpeg2k/color_conversion.cpp
        ${deps-libopenjpeg_SOURCE_DIR}/src/bin/common/color.c
    )
    add_compile_definitions(CUMED_DICOM_COMPRESSED)
    # libjpeg_turbo.cpp, libopenjpeg.cpp, color_conversion.cpp, color.c are pure
    # CPU code compiled by hipcc. CPATH may expose GCC x86 MMX/SSE intrinsic
    # headers that hipcc/clang rejects with unknown-builtin errors.
    # Undefine SIMD feature macros for these files so the GCC headers do not
    # emit __builtin_ia32_* builtins that clang doesn't know.
    set_source_files_properties(
        ${CUSLIDE_SRC}/cuslide/jpeg/libjpeg_turbo.cpp
        ${CUSLIDE_SRC}/cuslide/jpeg2k/libopenjpeg.cpp
        ${CUSLIDE_SRC}/cuslide/jpeg2k/color_conversion.cpp
        ${deps-libopenjpeg_SOURCE_DIR}/src/bin/common/color.c
        PROPERTIES COMPILE_OPTIONS
            "-U__MMX__;-U__SSE__;-U__SSE2__;-U__SSE3__;-U__SSSE3__;-U__SSE4_1__;-U__SSE4_2__;-U__AVX__;-U__AVX2__"
    )
    # Compile color.c as plain C so symbols keep C linkage (no name mangling).
    # libopenjpeg.cpp calls color_sycc_to_rgb etc. with C-linkage pointers, so
    # CXX compilation would produce mismatched mangled names and linker failures.
    # Matches what cucim.kit.cuslide does for the same file.
    set_source_files_properties(
        ${deps-libopenjpeg_SOURCE_DIR}/src/bin/common/color.c
        PROPERTIES LANGUAGE C
    )
endif()
add_library(${CUCIM_PLUGIN_NAME} ${CUMED_SRCS})

# Compile options
set_target_properties(${CUCIM_PLUGIN_NAME}
    PROPERTIES
        CXX_STANDARD 17
        CXX_STANDARD_REQUIRED YES
        CXX_EXTENSIONS NO
        SOVERSION ${PROJECT_VERSION_MAJOR}
        VERSION ${PROJECT_VERSION}
)
target_compile_features(${CUCIM_PLUGIN_NAME} PRIVATE cxx_std_17)
# Use generator expression to avoid `nvcc fatal   : Value '-std=c++17' is not defined for option 'Werror'`
#target_compile_options(${CUCIM_PLUGIN_NAME} PRIVATE $<$<COMPILE_LANGUAGE:CXX>:-Werror -Wall -Wextra>)
target_compile_definitions(${CUCIM_PLUGIN_NAME} PRIVATE __HIP_PLATFORM_AMD__)


# Link libraries
set(CUMED_LINK_LIBS deps::fmt deps::libdeflate hipcim::hipcim)
if(CUMED_DICOM_COMPRESSED)
    list(APPEND CUMED_LINK_LIBS deps::libjpeg-turbo deps::libopenjpeg deps::libopenjpeg-lcms2)
endif()
target_link_libraries(${CUCIM_PLUGIN_NAME} PRIVATE ${CUMED_LINK_LIBS})

target_include_directories(${CUCIM_PLUGIN_NAME}
        PUBLIC
            $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
            $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
        PRIVATE
            ${CMAKE_CURRENT_LIST_DIR}/src
            # turbojpeg.h + jconfig.h (generated) — only needed when JPEG decode is compiled
            $<$<BOOL:${CUMED_DICOM_COMPRESSED}>:${deps-libjpeg-turbo_SOURCE_DIR}>
            $<$<BOOL:${CUMED_DICOM_COMPRESSED}>:${deps-libjpeg-turbo_BINARY_DIR}>
            $<$<BOOL:${CUMED_DICOM_COMPRESSED}>:${CUSLIDE_SRC}>
            $<$<BOOL:${CUMED_DICOM_COMPRESSED}>:${deps-libopenjpeg_SOURCE_DIR}/src/lib/openjp2>
            $<$<BOOL:${CUMED_DICOM_COMPRESSED}>:${deps-libopenjpeg_BINARY_DIR}/src/lib/openjp2>
            $<$<BOOL:${CUMED_DICOM_COMPRESSED}>:${deps-libopenjpeg_SOURCE_DIR}/src/bin/common>
        )

# Do not generate SONAME as this would be used as plugin
# Need to use IMPORTED_NO_SONAME when using this .so file.
set_target_properties(${CUCIM_PLUGIN_NAME} PROPERTIES NO_SONAME 1)
# Prevent relative path problem of .so with no DT_SONAME.
# : https://stackoverflow.com/questions/27261288/cmake-linking-shared-c-object-from-externalproject-produces-binaries-with-rel
target_link_options(${CUCIM_PLUGIN_NAME} PRIVATE "LINKER:-soname=${CUCIM_PLUGIN_NAME}@${PROJECT_VERSION}.so")

# Do not add 'lib' prefix for the library
set_target_properties(${CUCIM_PLUGIN_NAME} PROPERTIES PREFIX "")
# Postfix version
set_target_properties(${CUCIM_PLUGIN_NAME} PROPERTIES OUTPUT_NAME "${CUCIM_PLUGIN_NAME}@${PROJECT_VERSION}")

################################################################################
# Add tests
#########################################################std#######################
add_subdirectory(tests)
add_subdirectory(benchmarks)

################################################################################
# Install
################################################################################
set(INSTALL_TARGETS
        ${CUCIM_PLUGIN_NAME}
        cumed_tests
        cumed_benchmarks
        )

install(TARGETS ${INSTALL_TARGETS}
        EXPORT ${CUCIM_PLUGIN_NAME}-targets
        RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
        COMPONENT ${CUCIM_PLUGIN_NAME}_Runtime
        LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
        COMPONENT ${CUCIM_PLUGIN_NAME}_Runtime
        NAMELINK_COMPONENT ${CUCIM_PLUGIN_NAME}_Development
        ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
        COMPONENT ${CUCIM_PLUGIN_NAME}_Development
        )

# Currently cumed plugin doesn't have include path so comment out
# install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/include/ DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
install(EXPORT ${CUCIM_PLUGIN_NAME}-targets
        FILE
        ${CUCIM_PLUGIN_NAME}-targets.cmake
        NAMESPACE
        ${PROJECT_NAME}::
        DESTINATION
        ${CMAKE_INSTALL_LIBDIR}/cmake/${CUCIM_PLUGIN_NAME})

# Write package configs
include(CMakePackageConfigHelpers)
configure_package_config_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/cmake/${CUCIM_PLUGIN_NAME}-config.cmake.in
    ${CMAKE_CURRENT_BINARY_DIR}/cmake/${CUCIM_PLUGIN_NAME}-config.cmake
    INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/${CUCIM_PLUGIN_NAME}
)
write_basic_package_version_file(
    ${CMAKE_CURRENT_BINARY_DIR}/cmake/${CUCIM_PLUGIN_NAME}-config-version.cmake
    VERSION ${PROJECT_VERSION}
    COMPATIBILITY AnyNewerVersion
)
install(
    FILES
        ${CMAKE_CURRENT_BINARY_DIR}/cmake/${CUCIM_PLUGIN_NAME}-config.cmake
        ${CMAKE_CURRENT_BINARY_DIR}/cmake/${CUCIM_PLUGIN_NAME}-config-version.cmake
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/${CUCIM_PLUGIN_NAME}
)


set(CMAKE_EXPORT_PACKAGE_REGISTRY ON)
export(PACKAGE ${CUCIM_PLUGIN_NAME})


# Write package configs
include(CMakePackageConfigHelpers)
configure_package_config_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/cmake/${CUCIM_PLUGIN_NAME}-config.cmake.in
    ${CMAKE_CURRENT_BINARY_DIR}/cmake/${CUCIM_PLUGIN_NAME}-config.cmake
    INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/${CUCIM_PLUGIN_NAME}
)
write_basic_package_version_file(
    ${CMAKE_CURRENT_BINARY_DIR}/cmake/${CUCIM_PLUGIN_NAME}-config-version.cmake
    VERSION ${PROJECT_VERSION}
    COMPATIBILITY AnyNewerVersion
)
install(
    FILES
        ${CMAKE_CURRENT_BINARY_DIR}/cmake/${CUCIM_PLUGIN_NAME}-config.cmake
        ${CMAKE_CURRENT_BINARY_DIR}/cmake/${CUCIM_PLUGIN_NAME}-config-version.cmake
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/${CUCIM_PLUGIN_NAME}
)

set(CMAKE_EXPORT_PACKAGE_REGISTRY ON) # TODO: duplicate?
export(PACKAGE ${CUCIM_PLUGIN_NAME})

unset(BUILD_SHARED_LIBS CACHE)
