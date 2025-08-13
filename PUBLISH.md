# Publish

## Publish a new official release

**Prerequisite**: Have a dataClay's pypi and testpypi account with owner access.

Pull the last code that has to be included in the release. Remember to use:

```bash
    git pull
    #and the following command to initialize the submodules
    git submodule update --init --recursive
```

or

```bash
    #if you only need to fetch the submodules
    git pull --recurse-submodules
```

1. Run `nox` to check lint and tests.
2. Push a new commit `release version <VERSION>` where you:
   - Update `dataclay.__version__` from `dataclay.__init__` to `<VERSION>`

3. Create and push a new tag:

   ```bash
   git tag -a <VERSION> -m "Release <VERSION>"
   git push origin <VERSION>
   ```

4. Follow the instructions to create a [new release](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository) in GitHub.

5. Publish the `dataclay:latest` docker image:

    1. First, generate a Personal Access Token (PAT) on GitHub (if you don't have):
        - Go to [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens).
        - Select **Tokens (classic)** or fine-grained tokens (depending on GitHub updates).
        - Click **Generate new token** and configure:
            - **Scopes**: At least select the `read:packages` and `write:packages`.
        - Generate the token and copy it (you’ll need it for the login).

    2. Then, log in to GitHub Packages (ghcr.io) with your account name and token:

        ```bash
        docker login ghcr.io
        ```

    3. Build and publish the docker image. To use `buildx` you may need to `sudo apt install qemu-user-static`:

        ```bash
        # Set the version variable
        VERSION=<VERSION>

        # Create a new builder instance
        export DOCKER_BUILDKIT=1
        docker buildx create --use

        # Build and push Python 3.9 bookworm
        docker buildx build --platform linux/amd64,linux/arm64 \
        -t ghcr.io/bsc-dom/dataclay:$VERSION-py3.9-bookworm \
        --build-arg PYTHON_VERSION=3.9-bookworm --push .

        # Build and push Python 3.10 bookworm
        docker buildx build --platform linux/amd64,linux/arm64 \
        -t ghcr.io/bsc-dom/dataclay:$VERSION-py3.10-bookworm \
        -t ghcr.io/bsc-dom/dataclay:$VERSION \
        -t ghcr.io/bsc-dom/dataclay:latest \
        --build-arg PYTHON_VERSION=3.10-bookworm --push .

        # Build and push Python 3.11 bookworm
        docker buildx build --platform linux/amd64,linux/arm64 \
        -t ghcr.io/bsc-dom/dataclay:$VERSION-py3.11-bookworm \
        --build-arg PYTHON_VERSION=3.11-bookworm --push .

        # Build and push Python 3.12 bookworm
        docker buildx build --platform linux/amd64,linux/arm64 \
        -t ghcr.io/bsc-dom/dataclay:$VERSION-py3.12-bookworm \
        --build-arg PYTHON_VERSION=3.12-bookworm --push .

        # Repeat for Python 3.9 and 3.10 with the _legacy dependency flavour_
        # Build and push Python 3.9 bookworm
        docker buildx build --platform linux/amd64,linux/arm64 \
        -t ghcr.io/bsc-dom/dataclay:$VERSION-legacydeps-py3.9-bookworm \
        --build-arg PYTHON_VERSION=3.9-bookworm \
        --build-arg LEGACY_DEPS=True \
        --push .

        # Build and push Python 3.10 bookworm
        docker buildx build --platform linux/amd64,linux/arm64 \
        -t ghcr.io/bsc-dom/dataclay:$VERSION-legacydeps-py3.10-bookworm \
        -t ghcr.io/bsc-dom/dataclay:$VERSION-legacydeps \
        --build-arg PYTHON_VERSION=3.10-bookworm \
        --build-arg LEGACY_DEPS=True \
        --push .
        ```

6. Publish the release distribution to PyPI:

    > **WARNING**  
    > If you encounter errors about duplicate filenames in the wheel archive during publishing, it's likely because protobuf files exist both in `src/dataclay/proto/` (pre-generated) and in the temporary directory created by the `compile_protos.py` build hook.  
    > **Temporary Solution:** Remove the pre-generated protobuf files from `src/dataclay/proto/` before building. The build hook will generate fresh files during the build, and these are included in the wheel automatically. Keeping pre-generated files in the source tree is unnecessary and causes conflicts.

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
- Update orchestration/spack to point the new version in PyPI

8. Update the _active versions_ on ReadTheDocs, i.e. go to the [versions page](https://readthedocs.org/projects/dataclay/versions/) and activate/deactivate versions accordingly. You probably must add the newly added release, and maybe you will need to deactivate patch versions that are irrelevant.

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
