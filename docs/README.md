# dataClay Documentation

The dataClay documentation is generated using [Sphinx](https://www.sphinx-doc.org/en/master/). The documentation is written in reStructuredText format and is located in the `dataclay/docs` directory.

## Manual Deployment

In order to generate the documentation, you need to install the following dependencies:

```bash
pip install -e .[docs]
```

Then, you can generate the documentation by running:

```bash
make html
```

The documentation will be generated in the `dataclay/docs/_build/html` directory. You can open the `index.html` file in your browser to view the documentation.

## Automatic Deployment

The documentation is automatically deployed using the `.readthedocs.yml` configuration file. The deployment is triggered whenever a new commit is pushed to the `main` branch. The deployed documentation is available at [https://dataclay.readthedocs.io/en/latest/](https://dataclay.readthedocs.io/en/latest/).
