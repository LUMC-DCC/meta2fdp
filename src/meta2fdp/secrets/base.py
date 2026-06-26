from abc import ABCMeta, abstractmethod


class SecretsProvider(metaclass=ABCMeta):
    @abstractmethod
    def get_info(self, name: str) -> str:
        raise NotImplementedError
