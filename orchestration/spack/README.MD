# SPACK

Copy `py-dataclay` and `py-opentelemetry-api` into `~/spack/var/spack/repos/<reponame>/packages/`

Install package with
```bash
spack install py-dataclay
spack install py-opentelemetry-api
```

Load package with
```bash
spack load py-dataclay
spack load py-opentelemetry-api
```

It may be necessary to `spack load py-deprecated` for py-opentelemetry-api.

If this error appears `C++ compiler supports templates for STL... configure: error: no` , remove from `~/.spack/linux/compilers.yaml` the compiler that don't have `cxx` field.