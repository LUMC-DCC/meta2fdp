from abc import ABCMeta, abstractmethod


class SecretsProvider(metaclass=ABCMeta):
    @abstractmethod
    def get(self, name: str) -> str:
        raise NotImplementedError
