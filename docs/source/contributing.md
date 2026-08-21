# Contributing to meta2fdp

Thank you for your interest in contributing to `meta2fdp`! This project is designed to make publishing metadata to FAIR Data Point instances easier and more extensible.

This page explains how to contribute new functionality, documentation, and tests to the `meta2fdp` project.

## Ways to contribute

- Fix bugs or improve reliability
- Add new connectors, extractors, or transformers
- Improve documentation and examples
- Add tests for new functionality
- Improve packaging, CI, or developer workflows

## Contribution workflow

1. Fork the repository and clone your fork.
2. Install the project and development dependencies.
3. Create a feature branch:

```bash
git checkout -b feature/my-new-connector
```

4. Add tests and documentation.
5. Open a pull request with a clear description and sample usage.

## Getting started

Install dependencies using the existing project configuration:

```bash
git clone https://github.com/FAIRDataTeam/meta2fdp.git
cd meta2fdp
uv sync
python -m pip install -e .
```

If you do not use `uv`, installing via `pip` is also supported:

```bash
python -m pip install -e .
```

Run tests locally:

```bash
python -m pytest
```

## What to contribute

- new connectors for source systems
- new extractors for structured or tabular input
- new transformer or schema modules
- new FDP client support for alternative publishing endpoints
- bug fixes and quality improvements
- documentation and examples

## Project structure

This package is organized around these extension points:

- `src/meta2fdp/connectors/` — source system connectors
- `src/meta2fdp/extractors/` — raw data extractors
- `src/meta2fdp/transformers/` — schema transformers and RDF conversion
- `src/meta2fdp/fdp/` — FAIR Data Point client integration
- `src/meta2fdp/config/` — typed configuration objects for pipelines and modules

## Adding a new module

1. Choose the extension point: connector, extractor, transformer, or FDP client.
2. Implement the new class under the appropriate package.
3. Register the implementation in the project registry or create a new registry entry, following the existing module structure and registration patterns.
4. Add tests under `tests/` to verify your new module.
5. Document the new module in the user guide or extension documentation.

## Documentation updates

Add or update the relevant docs in `docs/source/`:

- `extension_guide.md`
- `pipeline_usage.md`
- `user_guide.md`
- `dev_guide.md`

When adding a feature, update the relevant documentation in one of these files:

- `docs/source/user_guide.md`
- `docs/source/dev_guide.md`
- `docs/source/extension_guide.md`
- `docs/source/pipeline_usage.md`

## Code style

- Use idiomatic Python and follow existing project conventions
- Keep documentation up to date with code changes
- Add tests for new behavior and regression coverage

## LLM based development

Any pull request that has been created with the help of a Large Language model (LLM) must include a statement in the PR description that clearly indicates that an LLM was used to generate code or documentation. Code within the pull request has to be veriewable by humans within a reasonable time span. Writers of the pull request must ensure that the generated code is correct, secure, and adheres to the project's coding standards. LLM's must identify themselves in the text when generating pull request. This is to ensure transparency and maintain the integrity of the codebase.

## License

By contributing to this repository, you agree that your contributions will be licensed under the project's existing license.
