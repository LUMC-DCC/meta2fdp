"""This pipeline publishes metadata to the FDP server. It reads metadata from input files, converts it to RDF format, and posts it to the FDP server."""

from importlib import import_module
from typing import Any

import logging
from rdflib import URIRef

from meta2fdp.config.connector.base import ConnectorConfig
from meta2fdp.config.extractor.extractor import ExtractorConfig
from meta2fdp.pipeline.base import Pipeline
from meta2fdp.config.transformer.transformer import TransformerConfig
from meta2fdp.config.fdp.fdpconfig import FDPConfig


class PublishCatalogsDatasetsMetadataPipeline(Pipeline):
    """Pipeline for publishing metadata to the FDP server. This pipeline includes components for authentication, metadata extraction, RDF conversion, and posting to the FDP server."""

    def __init__(
        self,
        connector_config: ConnectorConfig | None = None,
        extractor_config: ExtractorConfig | None = None,
        schema_config: TransformerConfig | None = None,
        FDP_config: FDPConfig | None = None,
        registries: dict | None = None,
        secrets_providers: dict | None = None,
    ):
        """Initialize the PublishMetadataPipeline with provided configurations and module registries.

        Parameters:
            connector_config: Connector configuration object for selecting and initializing the connector.
            extractor_config: Extractor configuration object for selecting and initializing the extractor.
            schema_config: Transformer configuration object for selecting and initializing the schema module.
            FDP_config: FDP client configuration object for selecting and initializing the FDP client.
            registries: A dictionary of module registries for models, connectors, extractors, FDP clients, and secrets providers.
            secrets_providers: A dictionary of secrets providers to use for retrieving sensitive information such as API keys and credentials.
        """
        self.connector_config = connector_config
        self.extractor_config = extractor_config
        self.schema_config = schema_config
        self.FDP_config = FDP_config
        self.registries = registries or {}
        self.secrets_providers = secrets_providers or {}
        self.schema_module = self._resolve_schema() if self.schema_config else None

    def _resolve_schema(self):
        """Resolve the metadata schema module from the model registry based on the schema configuration."""
        model_registry = self.registries.get("models")
        if model_registry is None:
            raise KeyError("No model registry registered under 'models'.")
        return model_registry.get(
            self.schema_config.schema_name,
            self.schema_config.schema_version,
        )

    def _resolve_connector(self):
        connectors = self.registries.get("connectors", {})
        if self.connector_config is None:
            return None
        connector_cls = connectors.get(self.connector_config.connector_type)
        if connector_cls is None:
            raise KeyError(
                f"Connector type '{self.connector_config.connector_type}' is not registered."
            )
        return connector_cls(self.connector_config)

    def _resolve_extractor(self):
        extractors = self.registries.get("extractors", {})
        if self.extractor_config is None:
            return None
        extractor_cls = extractors.get(self.extractor_config.extractor_type)
        if extractor_cls is None:
            raise KeyError(
                f"Extractor type '{self.extractor_config.extractor_type}' is not registered."
            )
        return extractor_cls(self.extractor_config)

    def _resolve_fdp_client(self):
        clients = self.registries.get("fdp_clients", {})
        if self.FDP_config is None or not getattr(self.FDP_config, "name", None):
            return None
        return clients.get(self.FDP_config.name)(self.FDP_config)

    def run(self) -> Any:
        """Run the PublishMetadataPipeline by resolving registered modules and executing the pipeline flow."""
        print("Running PublishMetadataPipeline...")

        connector = self._resolve_connector()
        extractor = self._resolve_extractor()

        if connector is None or extractor is None or self.schema_config is None:
            raise ValueError(
                "Connector, extractor, and schema converter must be properly configured and resolved."
            )

        if self.schema_module is None:
            raise ValueError(
                "Schema module must be properly configured and resolved from the registry."
            )

        schema_cls = getattr(self.schema_module, "Hriv2Schema", None)
        if schema_cls is None:
            try:
                schema_cls = getattr(
                    import_module(f"{self.schema_module.__name__}.hriv2schema"),
                    "Hriv2Schema",
                )
            except Exception as exc:
                raise ValueError(
                    "Schema converter must be properly configured and resolved."
                ) from exc

        schema_converter = schema_cls(self.schema_config)

        client = self._resolve_fdp_client()
        if client is None or not hasattr(client, "get_api_token"):
            logging.critical("No valid FDP client configured, skipping authentication.")
            raise ValueError(
                "FDP client is not properly configured or does not have a get_api_token method."
            )

        client.get_api_token()

        if hasattr(client, "connection_status") and client.connection_status() != 200:
            raise ConnectionError("Unable to connect to FDP")

        if self.FDP_config is None or not getattr(self.FDP_config, "URL", None):
            raise ValueError("FDP config must provide an fdp_url.")

        catalog_df = connector.get_catalog()
        dataset_df = connector.get_dataset()

        parsed_catalogs = extractor.parse_catalog(catalog_df)

        parsed_datasets = None
        if hasattr(extractor, "parse_dataset"):
            try:
                parsed_datasets = extractor.parse_dataset(dataset_df)
            except Exception:
                parsed_datasets = None

        # Set up a lookup for datasets by their parsed identifier.
        dataset_lookup = None
        if parsed_datasets is not None and len(parsed_datasets) > 0:
            dataset_lookup = {
                row["identifier"]: row
                for row in parsed_datasets
                if row.get("identifier") is not None
            }

        for catalog_metadata in parsed_catalogs:
            contact_point = schema_converter.instantiate_vcard(catalog_metadata)
            publisher = schema_converter.instantiate_agent(
                catalog_metadata, "publisher"
            )
            catalog_class = schema_converter.instantiate_catalog(
                metadata=catalog_metadata,
                contact_point=contact_point,
                publisher=publisher,
            )

            catalog_graph = schema_converter.convert_class_to_rdf(
                catalog_class,
                URIRef(f"{self.FDP_config.URL}/new"),
            )
            catalog_graph.add(
                (
                    URIRef(f"{self.FDP_config.URL}/new"),
                    URIRef("http://purl.org/dc/terms/isPartOf"),
                    URIRef(self.FDP_config.URL),
                )
            )
            catalog_ttl = catalog_graph.serialize()
            catalog_url = client.post_resource(catalog_ttl, resource_type="catalog")
            if not catalog_url:
                logging.error("Failed to post catalog to FDP server.")
                raise ValueError("Catalog posting failed, no URL returned.")

            logging.info(f"Catalog posted successfully. URL: {catalog_url}")

            if hasattr(client, "publish_resource"):
                client.publish_resource(catalog_url)

            dataset_ids = catalog_metadata.get("dataset_ids", [])
            if isinstance(dataset_ids, str):
                dataset_ids = [
                    dataset_id.strip() for dataset_id in dataset_ids.split(",")
                ]

            for dataset_id in dataset_ids:
                if dataset_lookup is None or dataset_id not in dataset_lookup:
                    logging.debug(
                        f"Dataset '{dataset_id}' was not found in the parsed dataset metadata."
                    )
                    continue

                dataset_metadata = dataset_lookup[dataset_id]
                creators = [
                    schema_converter.instantiate_agent(dataset_metadata, "creator")
                ]
                contact_point = schema_converter.instantiate_vcard(
                    dataset_metadata,
                    "contactPoint",
                )
                publisher = schema_converter.instantiate_agent(
                    dataset_metadata, "publisher"
                )
                dataset_class = schema_converter.instantiate_dataset(
                    metadata=dataset_metadata,
                    contact_point=contact_point,
                    publisher=publisher,
                    creators=creators,
                )
                dataset_graph = schema_converter.convert_class_to_rdf(
                    dataset_class,
                    URIRef(f"{self.FDP_config.URL}/new"),
                )
                dataset_graph.add(
                    (
                        URIRef(f"{self.FDP_config.URL}/new"),
                        URIRef("http://purl.org/dc/terms/isPartOf"),
                        URIRef(catalog_url),
                    )
                )
                dataset_ttl = dataset_graph.serialize()
                dataset_url = client.post_resource(dataset_ttl, resource_type="dataset")
                if not dataset_url:
                    logging.error("Failed to post dataset to FDP server.")
                    raise ValueError("Dataset posting failed, no URL returned.")

                logging.info(f"Dataset posted successfully. URL: {dataset_url}")

                if hasattr(client, "publish_resource"):
                    client.publish_resource(dataset_url)
