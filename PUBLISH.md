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

```bash
python3 -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ dataClay
```

`--index-url` tell pip to download the package form TestPyPI instead of PyPI
`--extra-index-url` is used to install the package dependencies from PyPI


## Instructions for building and publishing Docker images

First, set up your personal access token and log in to GitHub Packages (ghcr.io)
```bash
export CR_PAT=YOUR_TOKEN
echo $CR_PAT | docker login ghcr.io -u USERNAME --password-stdin
```

Or just log in if the token is already stored:
```bash
docker login ghcr.io
```

**Release images:**
``` bash
VERSION={{ version form setup.cfg }}

# Python 3.10 bullseye
docker buildx build --platform linux/amd64,linux/arm64 \
-t ghcr.io/bsc-dom/dataclay:$VERSION-py3.10-bullseye \
-t ghcr.io/bsc-dom/dataclay:$VERSION \
-t ghcr.io/bsc-dom/dataclay:latest \
--build-arg PYTHON_VERSION=3.10-bullseye --push .
```

**Internal dev testing**
```bash
docker build -t ghcr.io/bsc-dom/dataclay:dev -f Dockerfile.dev \
--build-arg PYTHON_VERSION=3.10-bullseye .
```
To use buildx for different architectures you may need to install `QEMU` binaries. You can install them with:

```bash
sudo apt install qemu-user-static
```

## Release Steps

- Apply formatting and tests running `tox`
- Create a version tag with `git tag -a {VERSION} -m "Release {VERSION}"`
- Publish tag with `git push origin {VERSION}`
- Follow the instructions to publish the release to PyPI and Docker Hub.
- Update version from setup.cfg

