## Instructions for publishing into Pypi

Prerequisite: Have a dataClay's pypi account with owner access.

#### Publish to Pypi

It's strongly recommended to create a virtual environment and install requisites:

```
python3 -m pip install --upgrade setuptools wheel twine
python3 -m pip install -r requirements.txt
```

Execute `python3 setup.py egg_info --tag-build=dev --tag-date -q clean --all install sdist bdist_wheel` in order to create a development version.

Execute `python3 setup.py -q clean --all install sdist bdist_wheel` to create a Release.

Execute `twine upload dist/*` to upload to Pypi. 

