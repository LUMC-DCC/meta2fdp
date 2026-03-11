"""This pipeline publishes metadata to the FDP server. It reads metadata from input files, converts it to RDF format, and posts it to the FDP server."""

from meta2fdp.pipeline.base import Pipeline
from meta2fdp.config.schema import SchemaConfig


class PublishMetadataPipeline(Pipeline):
    """Pipeline for publishing metadata to the FDP server. This pipeline includes components for authentication, metadata extraction, RDF conversion, and posting to the FDP server."""

    def __init__(self, schema_config: SchemaConfig, registries: dict):
        """Initialize the PublishMetadataPipeline with the given schema configuration. The schema configuration specifies which metadata schema to use for RDF conversion.
        Parameters:
        schema_config (SchemaConfig): The configuration for the metadata schema to use.
        connector_config (ConnectorConfig): The configuration for the data connector to use for metadata extraction.
        extractor_config (ExtractorConfig): The configuration for the metadata extractor to use for metadata extraction.
        fdp_config (FDPConfig): The configuration for the FDP server to which the metadata will be posted.
        registries: A dictionary of registries for metadata schemas, connectors, and extractors.
        """

        self.schema_config = schema_config
        # TODO: add other configs: connector_config, extractor_config, fdp_config
        self.registries = registries

        self.schema_module = self._resolve_schema()

        def _resolve_schema(self):
            """Resolve the metadata schema module from the model registry based on the schema configuration."""
            return self.registries.models.get(
                self.schema_config.name, self.schema_config.version
            )

        def run(self):
            """Run the PublishMetadataPipeline by executing each component in sequence."""
            pass
