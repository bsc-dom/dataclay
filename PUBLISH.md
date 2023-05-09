# Publish

## Publish a new official release

**Prerequisite**: Have a dataClay's pypi and testpypi account with owner access.

1. Run `tox` to format and check tests.
2. Push a new commit `release version <VERSION>` where you:
   - Update `dataclay.__version__` from `dataclay.__init__` to `<VERSION>`
   - Add `Released YYYY-MM-DD` to `CHANGES.rst`

3. Create and push a new tag:
   ```bash
   git tag -a <VERSION> -m "Release <VERSION>"
   git push origin <VERSION>
   ```
4. Follow the instructions to create a [new release](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository) in GitHub.


5. Publish the `dataclay:latest` docker image:
    1. First, set up your personal access token and log in to GitHub Packages (ghcr.io):
        ```bash
        export CR_PAT=<YOUR_TOKEN>
        echo $CR_PAT | docker login ghcr.io -u USERNAME --password-stdin

        # Or just log if the token is already stored
        docker login ghcr.io
        ```
    2. Build and publish the docker image. To use `buildx` you may need to `sudo apt install qemu-user-static`:
        ``` bash
        # Set the version variable
        VERSION=<VERSION>

        # Build and push Python 3.10 bullseye
        docker buildx build --platform linux/amd64,linux/arm64 \
        -t ghcr.io/bsc-dom/dataclay:$VERSION-py3.10-bullseye \
        -t ghcr.io/bsc-dom/dataclay:$VERSION \
        -t ghcr.io/bsc-dom/dataclay:latest \
        --build-arg PYTHON_VERSION=3.10-bullseye --push .
        ```

6. Publish the release distribution to PyPI:

    ```bash
    # Create and source new virtual environment
    python3 -m venv venv.deploy && source venv.deploy/bin/activate

    # Install the latest `build` and `twine`
    python3 -m pip install --upgrade build twine

    # Remove `dist` folder if exists
    rm -rf dist/

    # Build the release distribution
    python3 -m build

    # Publish the package to TestPyPI
    # and check that everything works fine
    python3 -m twine upload --repository testpypi dist/*

    # Publish the package to PyPI
    python3 -m twine upload dist/*
    ```

7. Push a new commit `start version <NEW_VERSION>` where you:
   - Update `dataclay.__version__` from `dataclay.__init__` to `<NEW_VERSION>.dev`
   - Add new entry to `CHANGES.rst` with `<NEW_VERSION>`


## Publish a development distribution to TestPyPI

To build and publish a development distribution:

```bash
# Remove `dist` folder if exists
rm -rf dist/

# Set NUM_TAG to 0 and increment its value 
# to publish multiple builds on the same day
NUM_TAG=0

# Build the development distribution with date tag
python3 -m build -C--global-option=egg_info -C--global-option=--tag-date -C--global-option=--tag-build=$NUM_TAG

# Publish the package to TestPyPI
python3 -m twine upload --repository testpypi dist/*
```

To install a development package from TestPyPI use:

```bash
python3 -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ dataclay
```

- `--index-url` tells pip to download the package form TestPyPI instead of PyPI
- `--extra-index-url` is used to install the package dependencies from PyPI


## Build the dataclay dev image for testing

```bash
docker build -t ghcr.io/bsc-dom/dataclay:dev -f Dockerfile.dev \
--build-arg PYTHON_VERSION=3.10-bullseye .
```
