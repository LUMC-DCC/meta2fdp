from meta2fdp.secrets.base import SecretsProvider


class CompositeSecretsProvider(SecretsProvider):
    def __init__(self, providers):
        self.providers = providers

    def get_info(self, name: str) -> str:
        for p in self.providers:
            value = p.get(name)
            if value is not None:
                return value
        raise KeyError(f"Secret '{name}' not found")
