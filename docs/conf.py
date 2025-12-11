# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

import os

from importlib import metadata


# Set canonical URL from the Read the Docs Domain
html_baseurl = os.environ.get("READTHEDOCS_CANONICAL_URL", "")

# Tell Jinja2 templates the build is running on Read the Docs
if os.environ.get("READTHEDOCS", "") == "True":
    html_context = {"READTHEDOCS": True}


# We want an image in the README and include the README in the docs.
suppress_warnings = ["image.nonlocal_uri"]


# -- General configuration ----------------------------------------------------

extensions = [
    "myst_parser",
    "notfound.extension",
    "sphinx_copybutton",
    "sphinx.ext.autodoc",
    "sphinx.ext.autodoc.typehints",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
]

myst_enable_extensions = [
    "colon_fence",
    "smartquotes",
    "deflist",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix of source filenames.
source_suffix = [".rst", ".md"]

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "stamina"
author = "Hynek Schlawack"
copyright = f"2022, {author}"


# The full version, including alpha/beta/rc tags.
release = metadata.version("stamina")
# The short X.Y version.
version = release.rsplit(".", 1)[0]

if "dev" in release:
    release = version = "UNRELEASED"

exclude_patterns = ["_build"]

nitpick_ignore = [
    ("py:class", "httpx.HTTPError"),
    # ParamSpec is not well-supported.
    ("py:obj", "typing.~P"),
    ("py:class", "~P"),
    ("py:class", "stamina._core.T"),
]

# If true, '()' will be appended to :func: etc. cross-reference text.
add_function_parentheses = True

# Move type hints into the description block, instead of the func definition.
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"

# -- Options for HTML output --------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "furo"
html_theme_options = {
    "light_css_variables": {
        "font-stack": "system-ui, sans-serif",
        "font-stack--headings": "Bahnschrift, 'DIN Alternate', 'Franklin Gothic Medium', 'Nimbus Sans Narrow', sans-serif-condensed, sans-serif",
        "font-stack--monospace": "BerkeleyMono, MonoLisa, ui-monospace, "
        "SFMono-Regular, Menlo, Consolas, Liberation Mono, monospace",
    },
    # None of the options work, so we disable the button completely.
    "top_of_page_buttons": [],
}

html_static_path = ["_static"]
html_css_files = ["custom.css"]

htmlhelp_basename = "staminadoc"

_descr = "Production-grade retries made easy for Python."
_title = "stamina"
rst_epilog = f"""\
.. meta::
    :property=og:type: website
    :property=og:site_name: {_title}
    :property=og:description: {_descr}
    :property=og:author: Hynek Schlawack
    :twitter:title: {_title}
    :twitter:creator: @hynek
"""

linkcheck_ignore = [
    # GitHub has rate limits
    r"https://github.com/.*/(issues|pull|compare)/\d+",
    # Wikipedia has strict rate limits
    r"https://en.wikipedia.org/",
]

intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}
