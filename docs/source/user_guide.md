# User guide

`meta2fdp` is a Python framework for extracting metadata from source systems, transforming it into RDF, and publishing it to a FAIR Data Point.

## Installation

Install the package and dependencies:

```bash
uv sync
python -m pip install -e .
```

If you do not use `uv`, install directly with:

```bash
python -m pip install -e .
```

## Quick start

A simple usage pattern is to instantiate the publish pipeline with configured connectors, extractors, transformers, and FDP clients.

```python
from meta2fdp.config.connector.csvconnector import CSVConnectorConfig
from meta2fdp.config.extractor.extractor import ExtractorConfig
from meta2fdp.config.transformer.transformer import TransformerConfig
from meta2fdp.config.fdp.fdpconfig import FDPConfig
from meta2fdp.pipeline.publish_metadata import PublishMetadataPipeline
from meta2fdp.bootstrap import register_modules

registries = register_modules()

connector_config = CSVConnectorConfig(
    name="csv_connector",
    connector_name="CSVConnector",
    connector_type="csv",
    separator=";",
    header=0,
    catalog_input_file="tests/data/csv_connmap_test/catalog.csv",
    dataset_input_file="tests/data/csv_connmap_test/dataset.csv",
)

extractor_config = ExtractorConfig(
    name="df_extractor",
    config_type="extractor",
    extractor_name="DFExtractor",
    extractor_type="df",
    mapping_file="tests/config/mappings.yaml",
)

schema_config = registries["models"].get("HRIcore", "v2")

fdp_config = FDPConfig(
    name="sample_fdp_config",
    fdp_version="v2",
    URL="https://example-fdp.org",
)

pipeline = PublishMetadataPipeline(
    connector_config=connector_config,
    extractor_config=extractor_config,
    schema_config=schema_config,
    FDP_config=fdp_config,
    registries=registries,
)

pipeline.run()
```

## Configuration

Pipeline behavior is driven by typed configuration objects in `src/meta2fdp/config/`.

## Documentation

Build the docs with Sphinx from the root of the repository:

```bash
cd docs
sphinx-build -M html source build
```

## Notes

The package includes a small console entry point so that `meta2fdp` can be used to verify installation. The library is primarily intended to be used from Python code and from documented pipeline flows.