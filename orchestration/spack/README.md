# Spack Installation

Add the DataClay repository to Spack:
```bash
spack repo add dataclay/orchestration/spack
```

DataClay should be available as py-dataclay:
```bash
spack info py-dataclay
```
Install DataClay:
```bash
spack install py-dataclay
```

Load DataClay:
```bash
spack load py-dataclay
```

## Notes
If this error appears `C++ compiler supports templates for STL... configure: error: no` , remove from `~/.spack/linux/compilers.yaml` the compiler that don't have `cxx` field.

## Useful commands
```bash
spack find --loaded # Loaded packages
spack find -x # Packages explicitly installed 
spack find -X # installed dependencies
spack uninstall --all
spack unload --all
```
