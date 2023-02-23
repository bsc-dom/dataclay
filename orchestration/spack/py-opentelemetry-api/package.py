# Copyright 2013-2023 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

# ----------------------------------------------------------------------------
# If you submit this package back to Spack as a pull request,
# please first remove this boilerplate and all FIXME comments.
#
# This is a template package file for Spack.  We've put "FIXME"
# next to all the things you'll want to change. Once you've handled
# them, you can save this file and test your package like this:
#
#     spack install py-opentelemetry-api
#
# You can edit this file again by typing:
#
#     spack edit py-opentelemetry-api
#
# See the Spack documentation for more information on packaging.
# ----------------------------------------------------------------------------

from spack.package import *


class PyOpentelemetryApi(PythonPackage):
    """OpenTelemetry Python API"""

    # FIXME: Add a proper url for your package's homepage here.
    homepage = "https://github.com/open-telemetry/opentelemetry-python/tree/main/opentelemetry-api"
    pypi = "opentelemetry_api/opentelemetry_api-1.16.0.tar.gz"

    # FIXME: Add a list of GitHub accounts to
    # notify when the package is updated.
    # maintainers("github_user1", "github_user2")

    version("1.16.0", sha256="4b0e895a3b1f5e1908043ebe492d33e33f9ccdbe6d02d3994c2f8721a63ddddb")

    # FIXME: Only add the python/pip/wheel dependencies if you need specific versions
    # or need to change the dependency type. Generic python/pip/wheel dependencies are
    # added implicity by the PythonPackage base class.
    # depends_on("python@2.X:2.Y,3.Z:", type=("build", "run"))
    # depends_on("py-pip@X.Y:", type="build")
    # depends_on("py-wheel@X.Y:", type="build")

    # FIXME: Add a build backend, usually defined in pyproject.toml. If no such file
    # exists, use setuptools.
    depends_on("py-setuptools", type="build")
    depends_on("py-hatchling", type="build")
    depends_on("py-deprecated", type=("build", "run"))
