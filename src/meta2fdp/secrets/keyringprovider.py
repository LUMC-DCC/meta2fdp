from meta2fdp.secrets.base import SecretsProvider
import keyring


class KeyringSecretsProvider(SecretsProvider):
    """A secrets provider that retrieves secrets from the system keyring using the keyring library.
    This allows for secure storage and retrieval of secrets using the underlying keyring implementation of the operating system.
    """

    def get_info(self, service_name: str, username: str) -> str:
        return keyring.get_password(service_name, username)
