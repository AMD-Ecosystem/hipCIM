/*
 * SPDX-FileCopyrightText: Copyright (C) 2024-2026 Advanced Micro Devices, Inc. All rights reserved.
 * SPDX-License-Identifier: Apache-2.0
 *
 * hip_profile_shim.c -- LD_PRELOAD interposer that makes host-only LLVM
 * source-based coverage work on HIP code.
 *
 * Problem
 * -------
 * When AMD clang compiles a HIP translation unit with -fprofile-instr-generate
 * (even scoped to the host via -Xarch_host), it emits an offload "profile
 * shadow" variable named __llvm_profile_sections_<cuid> and registers it with
 * the HIP runtime via __hipRegisterVar. This is part of AMD's optional GPU
 * coverage support: the shadow variable is meant to have a matching device-side
 * symbol so device counters can be located.
 *
 * With host-only instrumentation there is no device-side __llvm_profile_sections
 * symbol, so when the HIP runtime tears down the fat binary it fails to bind the
 * registered variable and aborts the whole process:
 *
 *     :.../hipamd/src/hip_global.cpp:209 : Cannot create GlobalVar Obj for
 *         symbol: __llvm_profile_sections_<cuid>
 *     Aborted (core dumped)
 *
 * There is no compiler flag to suppress this registration, so this shim drops it
 * at runtime instead.
 *
 * Behavior
 * --------
 * __hipRegisterVar is interposed. Registrations for __llvm_profile_sections*
 * symbols are dropped; every other registration (genuine __device__ /
 * __constant__ / __managed__ variables) is forwarded unchanged to the real HIP
 * runtime via dlopen(RTLD_NOLOAD) + dlsym on the libamdhip64 handle. This
 * avoids the RTLD_NEXT link-order issue on manylinux/pip-based ROCm installs
 * where libamdhip64.so lives outside standard ld.so paths and isn't visible
 * to RTLD_NEXT from an LD_PRELOADed library. Dropping the shadow registration
 * is safe: host coverage counters are written by the LLVM profile runtime's
 * atexit handler, which is independent of HIP variable registration.
 *
 * Build:  gcc -O2 -fPIC -shared -o hip_profile_shim.so hip_profile_shim.c -ldl
 * Use:    LD_PRELOAD=hip_profile_shim.so <instrumented program>
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <string.h>
#include <unistd.h>

/* Matches the HIP runtime ABI for __hipRegisterVar (all args are pointers/ints,
 * so the exact const-qualification of the name arguments is irrelevant). */
typedef void (*hip_register_var_fn)(void **modules, char *var,
                                    const char *host_name,
                                    const char *device_name, int ext,
                                    unsigned long size, int constant,
                                    int global);

static const char kProfileShadowPrefix[] = "__llvm_profile_sections";

void __hipRegisterVar(void **modules, char *var, const char *host_name,
                      const char *device_name, int ext, unsigned long size,
                      int constant, int global)
{
    const unsigned long prefix_len = sizeof(kProfileShadowPrefix) - 1;

    /* Drop host-only LLVM coverage shadow variables: they have no device-side
     * counterpart and would abort the HIP runtime at fat-binary teardown. */
    if ((host_name && strncmp(host_name, kProfileShadowPrefix, prefix_len) == 0) ||
        (device_name && strncmp(device_name, kProfileShadowPrefix, prefix_len) == 0)) {
        return;
    }

    static hip_register_var_fn real_register_var = NULL;
    if (!real_register_var) {
        /* Use RTLD_NOLOAD to get a handle to the already-loaded libamdhip64
         * without risking infinite recursion (RTLD_DEFAULT would find ourselves)
         * or link-order failures (RTLD_NEXT can't see libs loaded via dlopen on
         * manylinux/pip-based ROCm where libamdhip64 lives outside ld.so paths). */
        void *hip = dlopen("libamdhip64.so", RTLD_NOLOAD | RTLD_NOW);
        if (hip) {
            real_register_var =
                (hip_register_var_fn)dlsym(hip, "__hipRegisterVar");
            dlclose(hip);
        }
        if (!real_register_var) {
            static const char msg[] =
                "hip_profile_shim: failed to resolve __hipRegisterVar in libamdhip64.so\n";
            write(STDERR_FILENO, msg, sizeof(msg) - 1);
            return;
        }
    }
    real_register_var(modules, var, host_name, device_name, ext, size,
                      constant, global);
}
