[![Build status](https://ci.appveyor.com/api/projects/status/g2q9140ejkt92b6m/branch/develop?retina=true)](https://ci.appveyor.com/project/support-dataclay/pyclay/branch/develop)
[![Build status](https://ci.appveyor.com/api/projects/status/g2q9140ejkt92b6m/branch/develop?svg=true&passingText=Passing+functional+tests&pendingText=Building+functional+tests)](https://dataclay.bsc.es/testing-report/)

[![Documentation Status](https://readthedocs.org/projects/pyclay/badge/?version=latest)](https://pyclay.readthedocs.io/en/latest/?badge=latest)
![PyPI - Status](https://img.shields.io/pypi/status/dataclay)
![PyPI - Format](https://img.shields.io/pypi/format/dataclay)
[![License](https://img.shields.io/github/license/bsc-dom/pyclay)](https://github.com/bsc-dom/pyclay/blob/develop/LICENSE.txt)
[![PyPI version](https://badge.fury.io/py/dataClay.png)](https://badge.fury.io/py/dataClay)
[![Pypi Downloads](https://pepy.tech/badge/dataclay)](https://pepy.tech/project/dataclay)
<br/>

[![Test Pypi](https://img.shields.io/badge/testpypi-2.7.dev-green)](https://test.pypi.org/project/dataClay/)

# dataClay Python codebase

This repository holds the `pyclay` Python package. This package is used both
by the dataClay Python clients and also for the dataClay service Execution
Environment.

## Installation

This package is available from PyPI, so just `pip` it:

    $ pip install dataClay

## Documentation

Official documentation available at [read the docs](https://pyclay.readthedocs.io/en/latest/)

## Packaging

Build and push the docker images for different Python versions and architectures.

``` bash
# Python 3.10 bullseye
docker buildx build --platform linux/amd64,linux/arm64 \
-t bscdataclay/dspython:2.7-py3.10-bullseye \
-t bscdataclay/dspython:2.7 \
-t bscdataclay/dspython:latest \
--build-arg PYTHON_VERSION=3.10-bullseye --push .

# Python 3.10 alpine
docker buildx build --platform linux/amd64,linux/arm64 \
-t bscdataclay/dspython:2.7-py3.10-alpine \
--build-arg PYTHON_VERSION=3.10-alpine --push .

# Python 3.10 slim
docker buildx build --platform linux/amd64,linux/arm64 \
-t bscdataclay/dspython:2.7-py3.10-slim \
--build-arg PYTHON_VERSION=3.10-slim --push .

# Python 3.8 bullseye
docker buildx build --platform linux/amd64,linux/arm64 \
-t bscdataclay/dspython:2.7-py3.8-bullseye \
--build-arg PYTHON_VERSION=3.8-bullseye --push .

# Python 3.8 alpine
docker buildx build --platform linux/amd64,linux/arm64 \
-t bscdataclay/dspython:2.7-py3.8-alpine \
--build-arg PYTHON_VERSION=3.8-alpine --push .

# Python 3.8 slim
docker buildx build --platform linux/amd64,linux/arm64 \
-t bscdataclay/dspython:2.7-py3.8-slim \
--build-arg PYTHON_VERSION=3.8-slim --push .
```

To generate development images use the following tag:
**devYYYYMMDD-py{version}-(bullseye|alpine|slim)**

For example:

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t bscdataclay/dev20220612-py3.10-bullseye \
--build-arg PYTHON_VERSION=3.10-bullseye --push .
```

To use buildx for different architectures you may need to install QEMU binaries. You can install them with:

```bash
sudo apt install qemu-user-static
```


## Other resources

[BSC official dataClay webpage](https://www.bsc.es/dataclay)

---

![dataClay logo](https://www.bsc.es/sites/default/files/public/styles/bscw2_-_simple_crop_style/public/bscw2/content/software-app/logo/logo_dataclay_web_bsc.jpg)
