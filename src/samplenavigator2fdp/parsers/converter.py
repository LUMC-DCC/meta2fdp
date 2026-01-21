"""Abstract class of a converter module. A class that dictates input and
output of any converter class. 
"""
from rdflib import Graph, Literal, URIRef, DCTERMS, XSD, Namespace
from pandas import Series
from abc import ABCMeta
from typing import  Union
from sempyro import LiteralField
from sempyro.dcat import DCATResource
from sempyro.hri_dcat import (
    HRICatalog, 
    HRIDataset, 
    HRIVCard, 
    HRIAgent, 
    HRIDistribution,
    HRIDataService,
    HRIDatasetSeries 
)



# TODO: factory function that generates a converter class based on available mappings:
# minimum information on mappings needed: fieldname/property, variable path, language
# mappping files are per resource

class Converter(metaclass=ABCMeta):

    def __init__(self) -> None:
        self.theme = None
        self.applicable_legislation = None
    
    def set_default_values(self, config: dict) -> None:
        """Set default values for resource properties.
        Should be per resource type or generic.

        :param config: A dictionary with default values. See config folder for structure.
        :type config: dict
        """
    
    def convert_class_to_rdf(self, HRIresource: DCATResource, uri: URIRef) -> Graph:
        """Converts the given HRI pydantic class to a graph where the
        subject uri is the URIRef. When uploading something new, that would be
        the FDP purl with a /new attached:
        https://fdp.xx/new

        :param HRIresource: A DCATResource class (HRI resources inherit this parent class)
        :type HRIresource: DCATResource
        :param uri: The subject uri that defines the class, either a fdp url with /new
        or the exact uri of the resource it should replace in the FDP
        :type uri: URIRef
        :return: A RDFLib Graph object containing the metadata of a resource
        :rtype: Graph
        """

    def metadata_to_agent(self, metadata: Series, agent_prefix: str) -> HRIAgent:
        """A function that uses the Series containing metadata and instantiates a
        SeMPyRO HRIAgent class. This could be information about a creator or publisher
         in a catalog for example.
        The implementation in the abstract function
        shows all possible inputs for the class. Mandatory properties have an
        example of accessing the Series for the appropriate values and converting
        them to the correct value type for that property.

        :param agent_prefix: The prefix used in the value labels that are associated with
        metatdat properties.
        :type agent_prefix: str
        :param metadata: A Series containing metadata about an Agent.
        :type metadata: Series
        :return: A SeMPyRO HRIAgent class which can be modified or converted to RDF.
        :rtype: HRIAgent
        """
        return HRIAgent(
        name=[LiteralField(value=metadata.loc[agent_prefix + "_name_en"], language="en"),
              LiteralField(value=metadata.loc[agent_prefix + "_name_nl"], language="nl")], #HACK this assumes that the metadata contains both en and nl language values
        identifier=[metadata.loc[agent_prefix + "_identifier"]],
        homepage=URIRef(metadata.loc[agent_prefix + "_url"]),
        mbox="mailto:" + metadata.loc[agent_prefix + "_email"],
        spatial=None,
        publisher_note=None,
        publisher_type=None
    )

    def metadata_to_HRIVcard(self, metadata: Series) -> HRIVCard:
        """A function that uses the Series containing metadata and instantiates a
        SeMPyRO HRIAgent class. HRIVCard's are used to define what values are
        associated to contactpoints in both Catalogs and Datasets. 
        The implementation in the abstract function
        shows all possible inputs for the class. Mandatory properties have an
        example of accessing the Series for the appropriate values and converting
        them to the correct value type for that property.

        :param metadata: A Series containing metadata about a contact point
        :type metadata: Series
        :return: _description_
        :rtype: HRIVCard
        """
        vcard=HRIVCard(
        hasEmail="mailto:" + metadata.loc["contactPoint_email"],
        formatted_name=metadata.loc["contactPoint_name"],
        hasUID=None,
        contact_page=None)
        return vcard


    def instantiate_HRICatalog(self, metadata: Series, creators: Union[list[HRIAgent], None], contact_point: HRIVCard, publisher: HRIAgent, service: Union[HRIDataService, None], url: URIRef) -> HRICatalog:
        """This a more generic sempyro catalog constructor that tries to build towards a more flexible
        generation of catalogs. The main point of doing this is to seperate different classes into their own functions.
        

        :param metadata: The metadata of a catalog
        :type metadata: Series
        :param creators: A catalog can have 0 or more creators, which are a described as agents
        :type creators: Union[list[HRIAgent], None]
        :param contact_point: A catalog has one contactpoint (for now) and is described with a Vcard
        :type contact_point: HRIVCard
        :param publisher: Publisher should be LUMC, see configuration for default values that could be used.
        :type publisher: HRIAgent
        :param service: Possible dataservice where distribution access is serviced.
        :type service: Union[HRIDataService, None]
        :param url: Subject url / internal URL to be used to represtent the catalog
        :type url: URIRef
        :return: Catalog class for reuse or manipulation
        :rtype: HRICatalog
        """
        # TODO switch creators to attributions (creators are specifically creators of the catalog e.g. LUMC not the authors of a study)
        catalog = HRICatalog(
            title=[
                LiteralField(value=metadata.loc["title_en"], language="en"),
                LiteralField(value=metadata.loc["title_nl"], language="nl")
            ],
            description=[
                LiteralField(value=metadata.loc["description_en"], language="en"),
                LiteralField(value=metadata.loc["description_nl"], language="nl")
            ],
            creator=creators,
            contact_point=contact_point,
            publisher=publisher,
            service=service,
            dataset=[])
        return catalog

    
    def instantiate_dataset(self, metadata: Series, creators: Union[list[HRIAgent], None], contact_point: HRIVCard, publisher: HRIAgent):
        dataset = HRIDataset(
        contact_point=contact_point,
        creator=creators,
        description=[LiteralField(value=metadata.loc["description_en"]),
                     LiteralField(value=metadata.loc["description_nl"])],
        #release_date=parser.isoparse("2024-07-01T11:11:11Z"),
        identifier=str(metadata.loc["identifier"]),
        #modification_date=parser.isoparse("2024-06-04T13:36:10Z"),
        publisher=publisher,
        theme=[URIRef("http://publications.europa.eu/resource/authority/data-theme/" + metadata.loc["theme"])],
        title=[
        LiteralField(value=metadata.loc["title_en"]),
        LiteralField(value=metadata.loc["title_nl"])
        ],
        distribution=[], # not sure if this is ever needed, as a new distribution is automatically linked to it's dataset by the FDP
        access_rights=URIRef("http://publications.europa.eu/resource/authority/access-right/" + str(metadata.loc["accessRights"])),
        keyword=metadata.loc["keywords"].split(","), #HACK: assumes the keywords are stored as a comma seperated list
        applicable_legislation=[URIRef(metadata.loc["applicableLegislation"])],
        number_of_records=LiteralField(value=str(metadata.loc["numberOfRecords"]), datatype=XSD.nonNegativeInteger),
        number_of_unique_individuals=LiteralField(value=str(metadata.loc["numberOfUniqueIndividuals"]), datatype=XSD.nonNegativeInteger)
        )
        return dataset

    def instantiate_distribution(self, metadata, graph: Graph) -> HRIDistribution:
       raise NotImplementedError


    def instantiate_datasetseries(self, metadata, graph: Graph) -> HRIDatasetSeries:
       raise NotImplementedError


    def instantiate_dataservice(self, metadata, graph: Graph) -> HRIDataService:
       raise NotImplementedError


    