from meta2fdp.secrets.base import SecretsProvider
import keyring


class KeyringSecretsProvider(SecretsProvider):
    def __init__(self, service_name: str):
        """
        :param service_name: Service name in keyring  associated with pipeline name. This is used to retrieve secrets from keyring .
        :type service_name: str
        """
        self.service_name = service_name

    def get(self, name):
        return keyring.get_password(self.service_name, name)
