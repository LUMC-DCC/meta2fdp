# Developer guide

This project uses `uv` for dependency management and supports editable installs with `pip`.

## Install dependencies

```bash
uv sync
python -m pip install -e .
```

If you do not use `uv`, you can also install directly with:

```bash
python -m pip install -e .
```

## Development workflow

- Create a feature branch
- Add or update tests for new behavior
- Update documentation when behavior changes
- Run `python -m pytest` before opening a pull request

## Pre-commit hooks

Enable formatting and linting hooks with:

```bash
pre-commit install
```

## Tests

Run all tests with:

```bash
python -m pytest
```

## Submodules and local FDP testing

Some integration tests use Git submodules and local FDP fixtures. Initialize submodules with:

```bash
git submodule init
git submodule update
```

## Build documentation

```bash
rm -r docs/build/*
cd docs
sphinx-apidoc -o source/apidoc ../src/meta2fdp
sphinx-build -M html source build
```

If you are on Windows, use a terminal that supports the commands above or substitute the equivalent filesystem commands.

