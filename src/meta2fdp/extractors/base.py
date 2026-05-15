"""meta2fdp.parsers.abstractparser

This module defines the `AbstractParser` base class used by concrete
parsers in the project. It provides a small set of common utilities
and the abstract API that all parser implementations should provide.

Usage
-----
- Subclass `AbstractParser` and implement the abstract methods
    `get_metadata` and `parse_catalog` (and any methods you need).
- Use `_resolve_path()` to canonicalise and validate file paths.

Testing
-------
Provide a tiny concrete subclass in tests that implements the
abstract methods and exercise `_resolve_path()` and the method
signatures. See `tests/parsers/test_abstractparser.py` for an example.
"""

from abc import ABCMeta, abstractmethod
from pandas import DataFrame


class AbstractParser(metaclass=ABCMeta):
    """An abstract class that defines functions and behaviours desired
    from a parser module.
    """

    def __init__(self, config) -> None:
        self.config = config

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
        # TODO A datasetSeries does not have bidirectional connection to the dataset, we need to decide on a methodology on connecting these resources
        # datasets are connected to datasetSeries but the datasetSeries has no ownership connection the other way around.
        """A function that extracts datasetseries metadata from the configured source.

        :return: A collection of metadata on distribution resources
        :rtype: DataFrame
        """
        pass
