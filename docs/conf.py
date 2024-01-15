# This file is part of BinPickle.
# Copyright (C) 2020-2023 Boise State University
# Copyright (C) 2023-2024 Drexel University
# Licensed under the MIT license, see LICENSE.md for details.
# SPDX-License-Identifier: MIT

import os
import sys
sys.path.insert(0, os.path.abspath(".."))

import binpickle

project = "BinPickle"
copyright = "2023 Michael Ekstrand"
author = "Michael D. Ekstrand"

release = binpickle.__version__

extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinxext.opengraph",
]

source_suffix = ".rst"

pygments_style = "sphinx"
highlight_language = "python3"

html_theme = "furo"
html_theme_options = {
}
templates_path = ["_templates"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "numpy": ("https://docs.scipy.org/doc/numpy/", None),
    "numcodecs": ("https://numcodecs.readthedocs.io/en/stable/", None),
}

autodoc_default_options = {
    "members": True,
    "member-order": "bysource"
}
autodoc_typehints = "description"
