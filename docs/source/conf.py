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
]

templates_path = ["_templates"]
exclude_patterns = []


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

html_theme = "furo"
html_static_path = ["_static"]
