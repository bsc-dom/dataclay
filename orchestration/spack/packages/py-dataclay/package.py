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
#     spack install py-dataclay
#
# You can edit this file again by typing:
#
#     spack edit py-dataclay
#
# See the Spack documentation for more information on packaging.
# ----------------------------------------------------------------------------

from spack.package import *


class PyDataclay(PythonPackage):
    """dataClay is a distributed data store that enables applications to store and access objects
    in the same format they have in memory, and executes object methods within the data store.
    These two main features accelerate both the development of applications and their execution."""

    homepage = "https://dataclay.bsc.es/"
    pypi = "dataclay/dataclay-4.0.0.tar.gz"
    # pypi = "dataclay/dataclay-3.1.0.tar.gz"
    # pypi = "dataclay/dataclay-3.0.1.tar.gz"
    # pypi = "dataClay/dataClay-3.0.0a3.tar.gz"
    # pypi = "dataClay/dataClay-3.0.0a2.tar.gz"
    # pypi = "dataClay/dataClay-3.0.0a1.tar.gz"

    # FIXME: Add a list of GitHub accounts to
    # notify when the package is updated.
    # maintainers("github_user1", "github_user2")

    version("4.0.0", sha256="9e6293a9398205b70e2dafc9a280b47ff46d07c338243c7f01d8847cb046ee52")
    version("3.1.0", sha256="21b1e2301416d298bcee29d0b34e31a58c41bbb187f2881938e5a3a047c52405")
    version("3.0.1", sha256="0cb7fb53eb7196d8e18bf11fcb85c5a0f8f09643e739c1be6b2ecceb3f7303a4")
    version("3.0.0a3", sha256="ff50c7464717df16b961c9600eac1ff6c3ad5c11da38384e4d0d7b76649a0045")
    version("3.0.0a2", sha256="e653c1d8efa5b2afc4f7af2bafa6eab90e2208c65c5c3441504a642ecc0d86d6")
    version("3.0.0a1", sha256="3b563d9c0ec86b10f129257485aaf4cf0977440c76b05a6dc3493a8508717ed1")

    depends_on("python@3.10:", type=("build", "run"))
    # depends_on("py-pip@X.Y:", type="build")
    # depends_on("py-wheel@X.Y:", type="build")
    depends_on("py-setuptools", type="build")

    depends_on("py-grpcio", type=("build", "run"))
    depends_on("py-psutil", type=("build", "run"))
    depends_on("py-protobuf", type=("build", "run"))
    depends_on("py-redis", type=("build", "run"))
    depends_on("py-bcrypt", type=("build", "run"))
