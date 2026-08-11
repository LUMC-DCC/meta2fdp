# Extension Guide

`meta2fdp` is designed to be extended with additional source connectors, extractors, transformer modules, and FAIR Data Point client implementations.

## How the system is structured

The project separates concerns into specific packages:

- `src/meta2fdp/connectors/` — classes that establish connections to input systems
- `src/meta2fdp/extractors/` — classes that convert raw input into normalized data structures
- `src/meta2fdp/transformers/` — classes that map input data to schema objects and serialize RDF
- `src/meta2fdp/fdp/` — client classes that publish RDF payloads to FDP endpoints

The current pipeline uses registries and configuration objects to locate the right implementation for each stage.

## Adding a new connector

1. Create a new connector implementation in `src/meta2fdp/connectors/`.
2. Ensure the connector exposes a consistent interface for the pipeline, such as methods to read catalogs and datasets.
3. Register the connector in the project registry if the repository uses a centralized registration mechanism.
4. Add tests under `tests/` for your connector.

## Adding a new extractor

1. Create a new extractor under `src/meta2fdp/extractors/`.
2. Implement parsing logic that returns a normalized data structure such as `pandas.DataFrame`.
3. Add unit tests to verify parsing behavior for example inputs.

## Adding a new transformer

1. Add the transformer module under `src/meta2fdp/transformers/`.
2. Ensure the transformer can be selected by schema name and version.
3. Document the new schema and provide examples of how it is used.

## Adding a new FDP client

1. Create a new client class in `src/meta2fdp/fdp/`.
2. Follow the existing client interface for authentication and resource posting.
3. Add tests to verify connectivity behavior when configured with mock or local endpoints.

## Deprecated bootstrap registry

The legacy `src/meta2fdp/bootstrap.py` module is deprecated. New modules should be registered through explicit registry functions or configuration-driven registration rather than relying on the bootstrap loader.

## Documentation

Document your extension in `docs/source/extension_guide.md` and reference it from `README.md`.
