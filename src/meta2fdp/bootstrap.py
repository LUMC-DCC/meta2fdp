import meta2fdp.transformers.HRIcore.v2.hriv2schema as HRIcore_v2
from meta2fdp.connectors.csvconnector import CSVConnector
from meta2fdp.extractors.dfextractor import DFExtractor
from meta2fdp.fdp.fdpclient import FDPClient
from meta2fdp.secrets.environmentprovider import EnvSecretsProvider
from meta2fdp.secrets.keyringprovider import KeyringSecretsProvider
from meta2fdp.transformers.registry import TransformerRegistry

from meta2fdp.config.transformer.transformer import TransformerConfig


def register_transformers():
    registry = TransformerRegistry()
    registry.register("HRIcore", "v2", HRIcore_v2)
    return registry


def register_connectors():
    return {"csv": CSVConnector}


def register_extractors():
    return {"df": DFExtractor}


def register_fdps():
    return {"FDPClient": FDPClient}


def register_secrets():
    return {"env": EnvSecretsProvider, "keyring": KeyringSecretsProvider}


def register_modules():
    return {
        "models": register_transformers(),
        "connectors": register_connectors(),
        "extractors": register_extractors(),
        "fdp_clients": register_fdps(),
        "secrets": register_secrets(),
    }


def register_models():
    return register_transformers()


def register_transformer_configs():
    # potentially, this could be extended to read from a configuration file or database to dynamically register transformer configurations
    HRIcore_v2_LUMC = TransformerConfig(
        name="HRIcore_v2_LUMC",
        config_type="transformer",
        schema_name="HRIcore",
        schema_version="v2",
        default_values={},
        language_tags=["en", "nl"],
    )
    HRIcore_v2_LUMC.get_default_values("tests/config/default_values.yaml")
    return {"HRIcore_v2_LUMC": HRIcore_v2_LUMC}
