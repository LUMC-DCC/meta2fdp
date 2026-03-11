"""Abstract base class for pipeline components in the meta2fdp framework.
This module defines the Pipeline class, which manages the execution of a sequence of pipeline components."""

from abc import ABC, abstractmethod


class Pipeline(ABC):
    """Base class for pipelines in the meta2fdp framework. A pipeline consists of a sequence of components that are executed in order to process data and produce output."""

    @abstractmethod
    def run(self):
        """Run the pipeline by executing each component in sequence."""
        pass
