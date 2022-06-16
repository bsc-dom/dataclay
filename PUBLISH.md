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
