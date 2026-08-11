# Pipeline Usage

`meta2fdp` is built around a configuration-driven pipeline that connects source data, schema transformation, and FAIR Data Point publishing.

## Core pipeline

The main publish pipeline is implemented in `src/meta2fdp/pipeline/publish_metadata.py`.

It uses:

- a connector to read source data
- an extractor to parse raw data into normalized structures
- a transformer/schema module to map data into RDF
- an FDP client to publish the serialized RDF to an FDP endpoint

## Configuration

Pipeline behavior is configured by typed configuration objects in `src/meta2fdp/config/`.

Typical configuration classes include:

- `ConnectorConfig`
- `ExtractorConfig`
- `TransformerConfig`
- `FDPConfig`

## Running the pipeline from code

A typical usage pattern from Python looks like this:

```python
from meta2fdp.config.connector.base import ConnectorConfig
from meta2fdp.config.extractor.extractor import ExtractorConfig
from meta2fdp.config.transformer.transformer import TransformerConfig
from meta2fdp.config.fdp.fdpconfig import FDPConfig
from meta2fdp.pipeline.publish_catalogs_datasets_metadata import PublishCatalogsDatasetsMetadataPipeline
from meta2fdp.bootstrap import register_modules

registries = register_modules()

pipeline = PublishCatalogsDatasetsMetadataPipeline(
    connector_config=ConnectorConfig(...),
    extractor_config=ExtractorConfig(...),
    schema_config=TransformerConfig(...),
    FDP_config=FDPConfig(...),
    registries=registries,
)

pipeline.run()
```

## Extension and automation

To support custom workflows, add or swap modules in the registry and provide configuration values for the new implementation.

For example, a new CSV connector can be added under `src/meta2fdp/connectors/` and registered in the connector registry.

## Recommended workflow

1. Configure the connector, extractor, transformer, and FDP client.
2. Validate the configuration with unit tests.
3. Run the pipeline in a controlled environment.
4. Inspect logs for successful catalog and dataset publication.

## Notes

The current CLI entrypoint is intentionally minimal. The package is primarily intended for library usage with configuration-driven pipeline orchestration.