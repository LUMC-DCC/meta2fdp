import pandas as pd
from rdflib import Graph, URIRef, XSD
from sempyro.dcat import DCATResource
from meta2fdp.schemas.abstractmodel import AbstractModel
from sempyro import LiteralField
from sempyro.hri_dcat import (
    HRICatalog,
    HRIDataset,
    HRIVCard,
    HRIAgent,
)


class Hriv2Model(AbstractModel):
    def __init__(self, model_config) -> None:
        self.model_config = model_config

    def set_model_config(self, model_config: dict) -> None:
        self.model_config = model_config

    def convert_class_to_rdf(self, HRIresource: DCATResource, uri: URIRef) -> Graph:
        return HRIresource.to_graph(uri)

    def lang_literals(self, metadata: pd.Series, colname: str) -> list[LiteralField]:
        # TODO: This could become a factory function so less if/else
        #  statements are made through running the pipeline
        """This function tries to detect any column attributes based on the
        listed language tags listed in the configuration. If no language tagged
        properties are found, try to find non langtagged colnames.

        :param metadata: metadata of a single resource
        :type metadata: pd.Series
        :param colname: colname of the literal property
        :type colname: str
        :return: A list of literals in the form of a SeMPyRO model
        :rtype: list[LiteralField]
        """
        properties = []
        if colname in metadata.index:
            nolang_literal = LiteralField(value=metadata.loc[colname])
            properties.append(nolang_literal)
        else:
            for langtag in self.model_config["langtags"].split(","):
                property_colname = colname + "_" + langtag
                if property_colname in metadata.index:
                    langtagged_literal = LiteralField(
                        value=metadata.loc[property_colname], language=langtag
                    )
                    properties.append(langtagged_literal)
        if len(properties) == 0:
            raise IndexError(f"No {colname} property found in resource: {metadata}")
        return properties

    def instantiate_HRIVcard(
        self, metadata: pd.Series, prefix="contactPoint"
    ) -> HRIVCard:
        """Modified instantiation of HRIVcard that has the recommended values
        removed.

        :param metadata: A Series containing metadata about a contact point
        :type metadata: Series
        :param prefix: the prefix of the column names associated to contactpoint, defaults to "contactPoint"
        :type prefix: str, optional
        :return: A HRIVcard pydantic class
        :rtype: HRIVCard
        """
        vcard = HRIVCard(
            hasEmail="mailto:" + metadata.loc[prefix + "_email"],
            formatted_name=self.lang_literals(
                metadata, prefix + "_name"
            ).pop(),  # formatted_name accepts a single property
        )
        return vcard

    def instantiate_agent(self, metadata: pd.Series, agent_prefix: str) -> HRIAgent:
        """A function that uses the Series containing metadata and instantiates a
        SeMPyRO HRIAgent class. This could be information about a creator or publisher
         in a catalog for example.
        The implementation shows all possible inputs for the class. Mandatory properties have an
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
            name=self.lang_literals(metadata, agent_prefix + "_name"),
            identifier=[metadata.loc[agent_prefix + "_identifier"]],
            homepage=URIRef(metadata.loc[agent_prefix + "_url"]),
            mbox="mailto:" + metadata.loc[agent_prefix + "_email"],
        )

    def instantiate_HRICatalog(
        self, metadata: pd.Series, contact_point: HRIVCard, publisher: HRIAgent
    ) -> HRICatalog:
        """This a sempyro catalog constructor that tries to build a catalog resource description using
        the samplenavigator reference data as a default. See parent class for all possible options.

        :param metadata: The metadata of a catalog
        :type metadata: Series
        :param contact_point: A catalog has one contactpoint (for now) and is described with a Vcard
        :type contact_point: HRIVCard
        :param publisher: Publisher should be LUMC, see configuration for default values that could be used.
        :type publisher: HRIAgent
        :return: Catalog class for reuse or manipulation
        :rtype: HRICatalog
        """
        catalog = HRICatalog(
            title=self.lang_literals(metadata, "title"),
            description=self.lang_literals(metadata, "description"),
            contact_point=contact_point,
            publisher=publisher,
            dataset=[],
        )
        return catalog

    def instantiate_HRIDataset(
        self,
        metadata: pd.Series,
        contact_point: HRIVCard,
        publisher: HRIAgent,
        creators: list[HRIAgent],
    ):
        dataset = HRIDataset(
            title=self.lang_literals(metadata, "title"),
            description=self.lang_literals(metadata, "description"),
            # release_date=parser.isoparse("2024-07-01T11:11:11Z"),
            identifier=str(metadata.loc["identifier"]),
            # modification_date=parser.isoparse("2024-06-04T13:36:10Z"),
            contact_point=contact_point,
            creator=creators,
            publisher=publisher,
            theme=[
                URIRef(
                    "http://publications.europa.eu/resource/authority/data-theme/"
                    + metadata.loc["theme"]
                )
            ],
            access_rights=URIRef(
                "http://publications.europa.eu/resource/authority/access-right/"
                + str(metadata.loc["accessRights"])
            ),
            keyword=metadata.loc["keywords"].split(
                ","
            ),  # HACK: assumes the keywords are stored as a comma seperated list
            applicable_legislation=[URIRef(metadata.loc["applicableLegislation"])],
            number_of_records=LiteralField(
                value=str(metadata.loc["numberOfRecords"]),
                datatype=XSD.nonNegativeInteger,
            ),  # relevant in current samplenavigator usecase
            number_of_unique_individuals=LiteralField(
                value=str(metadata.loc["numberOfUniqueIndividuals"]),
                datatype=XSD.nonNegativeInteger,
            ),  # relevant in current samplenavigator usecase
            distribution=[],  # not sure if this is ever needed, as a new distribution is automatically linked to it's dataset by the FDP
        )
        return dataset
