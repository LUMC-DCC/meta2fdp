# Developer documentation

Python packages are installed with [`uv` Python package manager](https://docs.astral.sh/uv/).

```
# install missing packages with uv
uv add <package-name>

# for development dependencies
uv add --dev <package-name>
```

Enable pre-commit hooks for linting and formatting

```
pre-commit install
```

When running tests, submodules are used to deploy an FDP locally for testing. This requires **Docker**.

```
# initialize local configuration file for Git submodules and fetch data from projects
git submodule init
git submodule update
```

## Build documentation

```
# Clean existing doc files
rm -r docs/build/*
# Build documentation in docs/
make html
```