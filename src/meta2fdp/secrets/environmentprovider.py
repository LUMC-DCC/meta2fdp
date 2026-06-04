import os
from dotenv import load_dotenv
from meta2fdp.secrets.base import SecretsProvider
import logging


class EnvSecretsProvider(SecretsProvider):
    """A secrets provider that first tries to load environment variables from a .env file
    if none is found, it uses the standard environement to obtain environment variables
    This allows for flexibility in how secrets are provided, supporting both .env files and standard environment variables.
    """

    def __init__(self, env_path=None):
        self.env_path = env_path
        if self.env_path is not None:
            if __debug__:
                logging.debug(
                    f"EnvSecretsProvider: Loading environment variables from {self.env_path}"
                )
                load_dotenv(self.env_path, verbose=True)
            else:
                load_dotenv(self.env_path)

    def get(self, name: str) -> str:
        return os.getenv(name)
