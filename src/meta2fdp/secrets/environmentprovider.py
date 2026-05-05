from meta2fdp.secrets.base import SecretsProvider
import os


class EnvSecretsProvider(SecretsProvider):
    def get(self, name):
        return os.getenv(name)
