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

# Set NUM_TAG to 0 and increment its value 
# to publish multiple builds on the same day
NUM_TAG=0

# Build development distribution with date tag
python3 -m build -C--global-option=egg_info -C--global-option=--tag-date -C--global-option=--tag-build=$NUM_TAG

# Publish package to TestPyPI
python3 -m twine upload --repository testpypi dist/*
```

### Build and upload a *release* distribution to PyPI

Make sure to remove **dev** suffix from `setup.cfg` version.

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

VERSION=3.0.0-alpha.1

# Python 3.10 bullseye
docker buildx build --platform linux/amd64,linux/arm64 \
-t bscdataclay/dspython:$VERSION-py3.10-bullseye \
-t bscdataclay/dspython:$VERSION \
-t bscdataclay/dspython:latest \
--build-arg PYTHON_VERSION=3.10-bullseye --push .

# Python 3.8 bullseye
docker buildx build --platform linux/amd64,linux/arm64 \
-t bscdataclay/dspython:$VERSION-py3.8-bullseye \
--build-arg PYTHON_VERSION=3.8-bullseye --push .
```

<!-- NOT SUPPORTED```bash
# Python 3.10 alpine
docker buildx build --platform linux/amd64,linux/arm64 \
-t bscdataclay/dspython:$VERSION-py3.10-alpine \
--build-arg PYTHON_VERSION=3.10-alpine --push .

# Python 3.10 slim
docker buildx build --platform linux/amd64,linux/arm64 \
-t bscdataclay/dspython:$VERSION-py3.10-slim \
--build-arg PYTHON_VERSION=3.10-slim --push .

# Python 3.8 alpine
docker buildx build --platform linux/amd64,linux/arm64 \
-t bscdataclay/dspython:$VERSION-py3.8-alpine \
--build-arg PYTHON_VERSION=3.8-alpine --push .

# Python 3.8 slim
docker buildx build --platform linux/amd64,linux/arm64 \
-t bscdataclay/dspython:$VERSION-py3.8-slim \
--build-arg PYTHON_VERSION=3.8-slim --push .
``` -->

**Development images:**

```bash
docker buildx build --platform linux/amd64,linux/arm64 \
-t bscdataclay/pyclay:edge \
--build-arg PYTHON_VERSION=3.10-bullseye --push .
```

Internal testing
```bash
docker build -t bscdataclay/pyclay:edge \
--build-arg PYTHON_VERSION=3.10-bullseye .
```

To use buildx for different architectures you may need to install `QEMU` binaries. You can install them with:

```bash
sudo apt install qemu-user-static
```

## Pre Release

- Create a new branch from `main` called **release-{release_version}**.
- Remove **dev** from setup.cfg version.
- Autoformat with black `black -l 100 .` and isort `isort -l 100 .`
- Merge branch to `main` with a pull request.
- Create a tag to the merge commit with `git tag -a {VERSION} -m "Release {VERSION}"`
- Publish tag with `git push origin {VERSION}`
- Follow instructions to publish the release to PyPI and Docker Hub.

## Post Release

- Create a new branch from `main` called **prepare-{new_version}-dev**
- setup.cfg: Update version to **{new_version}-dev**
- PUBLISH.md: Update docker build instructions with the new version
- Merge branch to `main` with a pull request.
