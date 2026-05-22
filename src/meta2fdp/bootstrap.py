import meta2fdp.transformers.HRIcore.v2 as HRIcore_v2
from meta2fdp.connectors.csvconnector import CSVConnector
from meta2fdp.extractors.dfextractor import DFExtractor
from meta2fdp.fdp.fdpclient import FDPClient
from meta2fdp.secrets.environmentprovider import EnvSecretsProvider
from meta2fdp.secrets.keyringprovider import KeyringSecretsProvider
from meta2fdp.transformers.registry import TransformerRegistry


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
