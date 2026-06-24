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
            logging.debug(
                f"EnvSecretsProvider: Loading environment variables from {self.env_path}"
            )
            loaded = load_dotenv(self.env_path)
            if not loaded:
                raise FileNotFoundError(
                    f"environment file at: {self.env_path} not loaded! Are you sure that is the right path?"
                )

    def get_info(self, name: str) -> str:
        return os.getenv(name)
