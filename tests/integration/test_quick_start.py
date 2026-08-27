from meta2fdp.config.connector.csvconnector import CSVConnectorConfig
from meta2fdp.config.extractor.extractor import ExtractorConfig
from meta2fdp.config.fdp.fdpconfig import FDPConfig
from meta2fdp.pipeline.publish_catalogs_datasets_metadata import (
    PublishCatalogsDatasetsMetadataPipeline,
)
from meta2fdp.bootstrap import register_modules, register_transformer_configs
from pathlib import Path

registries = register_modules()
transformer_configs = register_transformer_configs()

connector_config = CSVConnectorConfig(
    name="csv_connector",
    connector_name="CSVConnector",
    connector_type="csv",
    separator=";",
    header=0,
    catalog_input_file=Path("tests/data/input/Health-RI_LUMC_catalogue.csv"),
    dataset_input_file=Path("tests/data/input/Health-RI_LUMC_datasets.csv"),
)

extractor_config = ExtractorConfig(
    name="df_extractor",
    config_type="extractor",
    extractor_name="DFExtractor",
    extractor_type="df",
    mapping_file=Path("tests/config/mappings_test.yaml"),
)
extractor_config.get_mappings()  # Load mappings from the specified mapping file

schema_config = transformer_configs["HRIcore_v2_LUMC"]

fdp_config = FDPConfig(
    name="FDPClient",
    fdp_version="v2",
    URL="http://localhost",
    environmentprovider=registries["secrets"]["env"](),
    keyringprovider=registries["secrets"]["keyring"](),
)

pipeline = PublishCatalogsDatasetsMetadataPipeline(
    connector_config=connector_config,
    extractor_config=extractor_config,
    schema_config=schema_config,
    FDP_config=fdp_config,
    registries=registries,
)

pipeline.run()
