from abc import ABCMeta, abstractmethod
from pandas import DataFrame
from pathlib import Path
from typing import Union
from os import PathLike


class AbstractParser(metaclass=ABCMeta):
    """An abstract class that defines functions and behaviours desired
    from a parser module.
    """
    def __init__(self, config) -> None:
        self.config = config

    def _resolve_path(self, p: Union[str, PathLike, Path]) -> Path:
        """
        Resolve and validate a filesystem path.

        :param p: Path-like object or string to resolve.
        :type p: str or os.PathLike or pathlib.Path
        :returns: Resolved pathlib.Path
        :rtype: pathlib.Path
        :raises FileNotFoundError: If the resolved path does not exist.
        """
        p = Path(p)
        p = p.expanduser().resolve(strict=False)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {p}")
        return p

    @abstractmethod
    def get_metadata(self, path: str) -> DataFrame:
        """A function that obtains the metadata of a resource.
        This could be a database query or a file that is read.
        For queries, this function should be extended with credentials.

        :param path: A path, URI or other that points to the location of the data
        :type path: str
        :return: Output should be a table where every row is an individual resource
        :rtype: DataFrame
        """
        pass

    @abstractmethod
    def parse_catalog(self) -> DataFrame:
        """A function that extracts catalog metadata from the configured source.

        :return: A collection of metadata on catalog resources
        :rtype: DataFrame
        """
        pass


    def parse_dataset(self) -> DataFrame:
        """A function that extracts dataset metadata from the configured source.

        :return: A collection of metadata on dataset resources
        :rtype: DataFrame
        """
        pass


    def parse_distribution(self) -> DataFrame:
        """A function that extracts distribution metadata from the configured source.

        :return: A collection of metadata on distribution resources
        :rtype: DataFrame
        """
        pass


    def parse_dataservice(self) -> DataFrame:
        """A function that extracts dataservice metadata from the configured source.

        :return: A collection of metadata on dataservice resources
        :rtype: DataFrame
        """
        pass


    def parse_datasetseries(self) -> DataFrame:
        #TODO A datasetSeries does not have bidirectional connection to the dataset, we need to decide on a methodology on connecting these resources
        # datasets are connected to datasetSeries but the datasetSeries has no ownership connection the other way around.
        """A function that extracts datasetseries metadata from the configured source.

        :return: A collection of metadata on distribution resources
        :rtype: DataFrame
        """
        pass