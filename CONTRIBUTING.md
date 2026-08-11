# Contributing to meta2fdp

Thank you for your interest in contributing to `meta2fdp`! This project is designed to make publishing metadata to FAIR Data Point instances easier and more extensible.

## Ways to contribute

- Fix bugs or improve reliability
- Add new connectors, extractors, or transformers
- Improve documentation and examples
- Add tests for new functionality
- Improve packaging, CI, or developer workflows

## Getting started

1. Fork the repository and clone your fork.
2. Install dependencies:

```bash
git clone https://github.com/FAIRDataTeam/meta2fdp.git
cd meta2fdp
uv sync
python -m pip install -e .
```

3. Create a feature branch:

```bash
git checkout -b feature/my-new-connector
```

4. Run tests locally:

```bash
python -m pytest
```

5. Open a pull request with a clear description and sample usage.

## Project structure

This package is organized into the following extension points:

- `src/meta2fdp/connectors/` — source system connectors
- `src/meta2fdp/extractors/` — raw data extractors
- `src/meta2fdp/transformers/` — schema transformers and RDF conversion
- `src/meta2fdp/fdp/` — FAIR Data Point client integration
- `src/meta2fdp/config/` — typed configuration objects for pipelines and modules

## Adding a new module

1. Choose the extension point: connector, extractor, transformer, or FDP client.
2. Implement the new class under the appropriate package.
3. Register the implementation in the project registry or create a new registry entry.
4. Add tests under `tests/` to verify your new module.
5. Document the new module in the user guide or extension documentation.

## Documentation updates

Add or update the relevant docs in `docs/source/`:

- `extension_guide.md`
- `pipeline_usage.md`
- `user_guide.md`
- `dev_guide.md`

## Code style

- Use idiomatic Python and follow existing project conventions
- Keep documentation up to date with code changes
- Add tests for new behavior and regression coverage

## License

By contributing to this repository, you agree that your contributions will be licensed under the project's existing license.
