# Contributing to meta2fdp

This page explains how to contribute new functionality, documentation, and tests to the `meta2fdp` project.

## Contribution workflow

1. Fork the repository and clone your fork.
2. Install the project and development dependencies.
3. Create a branch for your change.
4. Add tests and documentation.
5. Open a pull request.

## Recommended local setup

Use the existing project configuration to install dependencies:

```bash
uv sync
python -m pip install -e .
```

If you do not use `uv`, installing via `pip` is also supported:

```bash
python -m pip install -e .
```

## What to contribute

- new connectors for source systems
- new extractors for structured or tabular input
- new transformer or schema modules
- new FDP client support for alternative publishing endpoints
- bug fixes and quality improvements
- documentation and examples

## Documentation expectations

When adding a feature, update the docs in one of these files:

- `docs/source/user_guide.md`
- `docs/source/dev_guide.md`
- `docs/source/extension_guide.md`
- `docs/source/pipeline_usage.md`

## Extension points

The library is organized around clearly defined extension points:

- `connectors` — connect to data sources
- `extractors` — read and normalize raw data
- `transformers` — map normalized data into a schema and RDF
- `fdp` — publish RDF to a FAIR Data Point

New implementations should follow the existing module structure and registration patterns.
