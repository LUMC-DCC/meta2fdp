from abc import ABCMeta, abstractmethod
from rdflib import Graph, Literal, URIRef, DCTERMS, XSD, Namespace
from pandas import DataFrame, Series
from sempyro.hri_dcat import (
    HRICatalog, 
    HRIDataset, 
    HRIVCard, 
    HRIAgent, 
    HRIDistribution,
    HRIDataService,
    HRIDatasetSeries
)


class Parser(metaclass=ABCMeta):
    """An abstract class that defines functions and behaviours desired
    from a parser module.
    """
    def __init__(self) -> None:
        pass

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

    def parse_catalog(self, metadata: Series) -> Graph:
        """A function that extracts catalog metadata from the Series and
        uses these values to make a RFDLib Graph representation of
        the information within. 

        :param metadata: Labeled metadata values from a single catalog resource
        :type metadata: Series
        :return: A graph representation of a catalog resource
        :rtype: Graph
        """
        pass

    def parse_dataset(self, metadata: Series, catalog_id: str) -> Graph:
        """A function that extracts dataset metadata from the Series and
        uses these values to make a RFDLib Graph representation of
        the information within. Datasets in the FDP have by default
        a dcterms:isPartOf attribute that points to it's associated catalog.
        This is a mandatory property so ideally the catalog_id variable contains
        the PURL of the associated catalog. If parsing is done in batches, i.e.
        all resources from a source system are converted in RDF in one go, the
        catalog_id can also be an identifier that isn't formatted as a URI.

        :param metadata: A collection of labeled metadata of a single dataset
        :type metadata: Series
        :param catalog_id: An identifier that can be used to link the dataset to
          a catalog
        :type catalog_id: str
        :return: A graph representation of a dataset resource
        :rtype: Graph
        """
        pass
    
    def parse_datasetseries(self, metadata: Series, catalog_id: str, datasets_ids:list) -> Graph:
        #TODO A datasetSeries does not have bidirectional connection to the dataset, we need to decide on a methodology on connecting these resources
        # datasets are connected to datasetSeries but the datasetSeries has no ownership connection the other way around.
        """A function that extracts datasetSeries metadata from the Series and
        uses these values to make a RFDLib Graph representation of
        the information within. A datasetSeries is connected to a catalog and must have an catalog_id.
        

        :param metadata: A collection of labeled metadata of a single datasetSeries
        :type metadata: Series
        :param catalog_id:  An identifier that can be used to link the datasetSeries to
          a catalog
        :type catalog_id: str
        :param datasets_ids: Identifer(s) that are part of the datasetseries
        :type datasets_ids: list
        :return: An RDF representation of a datasetSeries resource
        :rtype: Graph
        """
        pass
    
    def parse_distribution(self, metadata: Series, dataset_id: str) -> Graph:
        """A function that extracts distribution metadata from the Series and
        uses these values to make a RFDLib Graph representation of
        the information within. 

        :param metadata: A collection of labeled metadata of a single datasetSeries
        :type metadata: Series
        :param dataset_id:  An identifier that can be used to link the distribution to
          a dataset
        :type dataset_id: str
        :return: An RDF representation of a distribution resource
        :rtype: Graph
        """
        pass

    def parse_dataservice(self, metadata: Series, distribution_id: str) -> Graph:
        """A function that extracts dataservice meatadata from the Series and
        uses these values to make an RDFLib Graph representation of the information
        within. 

        :param metadata: A collection of labeled metadata of a single dataservice
        :type metadata: Series
        :param distribution_id: An identifier that can be used to link the dataservice to
          a distribution
        :type distribution_id: str
        :return: An RDF representation of a dataservice resource
        :rtype: Graph
        """
        pass

    


    # This is technically a new class like RFDClient
    def upload_catalog(self, catalog_rdf:Graph) -> str:
        """A function that uploads a catalog resource
        graph representation to the designated FDP.
        This should contain all mandatory properties defined
        in the FDP SHACL for catalogs.
        (use FDPClient create_metadata function)

        :param catalog_rdf: A graph representation of a catalog resource with subject:
        <FDPURL>/new that complies to the SHACL on the FDP
        :type catalog_rdf: Graph
        :return: The location of the newly uploaded catalog
        :rtype: str
        """
        pass

    def publish_catalog(self, url:str):
        """A function that sets 

        :param url: _description_
        :type url: str
        """