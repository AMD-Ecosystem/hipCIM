#
# SPDX-FileCopyrightText: Copyright (C) 2024-2026 Advanced Micro Devices, Inc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import re

# rocm_docs fetches ROCm release labels from GitHub during config-inited. Stub those
# requests when TLS verification fails on networks with an inspecting proxy.
def _patch_rocm_docs_github_requests() -> None:
    import requests

    orig_get = requests.get
    stub_urls = {
        "https://raw.githubusercontent.com/ROCm/rocm-docs-core/data/latest_version.txt",
        "https://raw.githubusercontent.com/ROCm/rocm-docs-core/data/release_candidate.txt",
    }

    class _StubResponse:
        status_code = 200

        def __init__(self, text: str) -> None:
            self.text = text

    def get(url, *args, **kwargs):
        if url not in stub_urls:
            return orig_get(url, *args, **kwargs)
        try:
            return orig_get(url, *args, **kwargs)
        except requests.RequestException:
            return _StubResponse("")

    requests.get = get


_patch_rocm_docs_github_requests()

'''
html_theme is usually unchanged (rocm_docs_theme).
flavor defines the site header display, select the flavor for the corresponding portals
flavor options: rocm, rocm-docs-home, rocm-blogs, rocm-ds, instinct, ai-developer-hub, local, generic
'''
html_theme = "rocm_docs_theme"
# repository_url is set explicitly because the theme can only derive it from an
# https or git@host:org/repo remote, which SSH host aliases don't match.
html_theme_options = {
    "flavor": "rocm-ls",
    "repository_url": "https://github.com/AMD-Ecosystem/hipCIM",
}


# This section turns on/off article info
setting_all_article_info = True
all_article_info_os = ["linux"]
all_article_info_author = ""

# Dynamically extract component version
with open('../HIPCIM_VERSION', encoding='utf-8') as f:
    version_number = f.read()
    if not version_number:
        raise ValueError("VERSION not found!")

# for PDF output on Read the Docs
project = "hipCIM"
author = "Advanced Micro Devices, Inc."
copyright = "Copyright (C) 2024-2026 Advanced Micro Devices, Inc. All rights reserved."
version = version_number
release = version_number

external_toc_path = "./sphinx/_toc.yml" # Defines Table of Content structure definition path

# Use bundled projects.yaml for local builds; skip GitHub fetch for intersphinx mappings.
external_projects_current_project = "hipcim"

# Add more addtional package accordingly
extensions = [
    "rocm_docs",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autodoc",  # Automatically create API documentation from Python docstrings
    "sphinx.ext.autosummary",
    "sphinx.ext.doctest",
    "sphinx_copybutton",
]

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "special-members": "__init__, __getitem__",
    "inherited-members": True,
    "show-inheritance": True,
    "imported-members": False,
    "member-order": "bysource",  # bysource: seems unfortunately not to work for Cython modules
}

html_title = f"{project} {version_number}"
