# Publish

## Instructions for publishing into Pypi

**Prerequisite**: Have a dataClay's pypi and testpypi account with owner access.

### Prepare

It's strongly recommended to use a virtual environment.

Make sure you have the latest `build` and `twine` versions installed:

```bash
python3 -m pip install --upgrade build twine
```

### Build and upload a *development* distribution to TestPyPI

```bash
# Remove dist folder if exists
rm -rf dist/

# Build development distribution with date tag
python3 -m build -C--global-option=egg_info -C--global-option=--tag-date -C--global-option=--tag-build=dev

# Publish package to TestPyPI
python3 -m twine upload --repository testpypi dist/*
```

### Build and upload a *release* distribution to PyPI

```bash
# Remove dist folder if exists
rm -rf dist/

# Build release distribution
python3 -m build

# Publish package to PyPI
python3 -m twine upload dist/*
```

### Installing *development* package from TestPyPI

```
python3 -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ dataClay
```

`--index-url` tell pip to download the package form TestPyPI instead of PyPI
`--extra-index-url` is used to install the package dependencies from PyPI


## Instructions for building and publishing Docker images

**Release images:**

``` bash
# Python 3.10 bullseye
docker buildx build --platform linux/amd64,linux/arm64 \
-t bscdataclay/dspython:2.7-py3.10-bullseye \
-t bscdataclay/dspython:2.7 \
-t bscdataclay/dspython:latest \
--build-arg PYTHON_VERSION=3.10-bullseye --push .

# Python 3.8 bullseye
docker buildx build --platform linux/amd64,linux/arm64 \
-t bscdataclay/dspython:2.7-py3.8-bullseye \
--build-arg PYTHON_VERSION=3.8-bullseye --push .
```

<!-- NOT SUPPORTED```bash
# Python 3.10 alpine
docker buildx build --platform linux/amd64,linux/arm64 \
-t bscdataclay/dspython:2.7-py3.10-alpine \
--build-arg PYTHON_VERSION=3.10-alpine --push .

# Python 3.10 slim
docker buildx build --platform linux/amd64,linux/arm64 \
-t bscdataclay/dspython:2.7-py3.10-slim \
--build-arg PYTHON_VERSION=3.10-slim --push .

# Python 3.8 alpine
docker buildx build --platform linux/amd64,linux/arm64 \
-t bscdataclay/dspython:2.7-py3.8-alpine \
--build-arg PYTHON_VERSION=3.8-alpine --push .

# Python 3.8 slim
docker buildx build --platform linux/amd64,linux/arm64 \
-t bscdataclay/dspython:2.7-py3.8-slim \
--build-arg PYTHON_VERSION=3.8-slim --push .
``` -->

**Development images:**

To generate development images use the following tag:  
*devYYYYMMDD-py{version}-bullseye*

For example:

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t bscdataclay/dev20220612-py3.10-bullseye \
--build-arg PYTHON_VERSION=3.10-bullseye --push .
```

To use buildx for different architectures you may need to install `QEMU` binaries. You can install them with:

```bash
sudo apt install qemu-user-static
```

## Pre Release

Create release branch from `main`, update versions and create a pull request.

Create and publish a release tag to the new `main` commit with:

```bash
git tag -a {VERSION} -m "Release {VERSION}"

git push origin {VERSION}
```

Publish new release to PyPI and Docker Hub.

## Post Release

Update in `develop`:

- VERSION.txt
- PUBLISH.md instructions with new version
- README.md version
- setup.cfg version
