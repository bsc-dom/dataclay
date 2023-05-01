# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "dataClay"
copyright = "2023, BSC Distributed Object Management"
author = "BSC Distributed Object Management"
release = "3.0.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    # "sphinx.ext.linkcode",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# def linkcode_resolve(domain, info):
#     if domain != "py":
#         return None
#     if not info["module"]:
#         return None
#     module = info["module"].replace(".", "/")
#     fullname = info["fullname"].replace(".", "/")
#     # return "https://somesite/sourcerepo/%s.py" % filename
#     return f"https://github.com/bsc-dom/dataclay/blob/main/src/{module}.py"


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

html_theme = "furo"

html_static_path = ["_static"]

html_theme_options = {
    "sidebar_hide_name": True,
    "light_logo": "dataclay-name.png",
    "dark_logo": "dataclay-name.png",
}

html_favicon = "_static/dataclay-logo.png"


# Copy button

# For automatic exclusion, make sure to use the right highlight language.
# For example: pythonconsole instead of python, console instead of bash,
# ipythonconsole instead of ipython, etc.
copybutton_exclude = ".linenos, .gp"
