"""This module contains the implementation of the HRIV2Schema class, which is a specific schema for converting metadata into RDF format using the SeMPyRO library. The class provides methods for instantiating various SeMPyRO classes such as HRICatalog, HRIDataset, HRIVCard, and HRIAgent based on the provided metadata. It also includes a method for converting these classes into RDF graphs. The schema configuration can be set and updated as needed."""

import pandas as pd
from rdflib import Graph, URIRef, XSD
from sempyro.dcat import DCATResource
from meta2fdp.models.base import AbstractSchema
from sempyro import LiteralField
from sempyro.hri_dcat import (
    HRICatalog,
    HRIDataset,
    HRIVCard,
    HRIAgent,
)
from sempyro import RDFModel
from typing import Annotated
from pydantic import Field, create_model, AnyUrl
from pydantic_core._pydantic_core import PydanticUndefinedType

_Attrs = {
    "default": ...,
    "default_factory": None,
    "alias": None,
    "alias_priority": None,
    "validation_alias": None,
    "serialization_alias": None,
    "title": None,
    "field_title_generator": None,
    "description": None,
    "examples": None,
    "exclude": None,
    "discriminator": None,
    "deprecated": None,
    "json_schema_extra": None,
    "frozen": None,
    "validate_default": None,
    "repr": True,
    "init": None,
    "init_var": None,
    "kw_only": None,
}


class Hriv2Schema(AbstractSchema):
    def __init__(self, config: dict) -> None:
        self.config = config
        self.model_config = self.config["model_config"]
        self.default_values = self.config.get("default_values", {})
        self.langtags = self.model_config["langtags"].split(",")
        # Cache factory-generated model classes
        self._catalog_model = None
        self._dataset_model = None
        self._agent_model = None
        self._vcard_model = None

    def set_schema_config(self, config: dict) -> None:
        self.config = config
        self.model_config = self.config["model_config"]
        self.default_values = self.config.get("default_values", {})
        self.langtags = self.model_config["langtags"].split(",")
        # Reset cached models if config changes
        self._catalog_model = None
        self._dataset_model = None
        self._agent_model = None
        self._vcard_model = None

    def convert_class_to_rdf(self, HRIresource: DCATResource, uri: URIRef) -> Graph:
        return HRIresource.to_graph(uri)

    def lang_literals(self, metadata: pd.Series, colname: str) -> list[LiteralField]:
        """Create LiteralField objects from metadata, handling language tags.

        This function attempts to create LiteralField objects for a given column name
        from the metadata series. It first checks for a non-language-tagged value,
        then for language-tagged variants based on configured language tags in the schema.

        :param metadata: Metadata series containing resource properties.
        :type metadata: pd.Series
        :param colname: Base column name for the literal property.
        :type colname: str
        :return: List of LiteralField objects, each with appropriate language tag if applicable.
        :rtype: list[LiteralField]
        :raises Warning: If no matching property (tagged or untagged) is found in the metadata.
        """
        properties = []
        if colname in metadata.index:
            nolang_literal = LiteralField(value=metadata.loc[colname])
            properties.append(nolang_literal)
        else:
            for langtag in self.langtags:
                property_colname = colname + "_" + langtag
                if property_colname in metadata.index:
                    langtagged_literal = LiteralField(
                        value=metadata.loc[property_colname], language=langtag
                    )
                    properties.append(langtagged_literal)
        if len(properties) == 0:
            raise Warning(f"No {colname} property found in resource: {metadata}")
        return properties

    def untag_defaults(self, defaults: dict, langtags: list):
        """Remove language tags from dictionary keys.

        This function processes a dictionary of default values by stripping
        language tags (e.g., '_en', '_nl') from the keys, resulting in a set
        of tagless keys.

        :param defaults: Dictionary with keys that may include language tags.
        :type defaults: dict
        :param langtags: List of language tag strings to remove from keys.
        :type langtags: list
        :return: A set of keys with language tags removed.
        :rtype: set
        """
        tagless_keys = set()
        for key in defaults.keys():
            for langtag in langtags:
                key = key.split("_" + langtag)[0]
            tagless_keys.add(key)
        return tagless_keys

    def set_defaults(self, model_cls: type[RDFModel], defaults: dict) -> type[RDFModel]:
        """Set default values for model fields based on configuration.

        This function creates a new Pydantic model class with default values
        applied to fields that don't have defaults set. It handles language-tagged
        literals and URI fields appropriately.

        :param model_cls: The base RDFModel class to modify.
        :type model_cls: type[RDFModel]
        :param defaults: Dictionary of default values, potentially with language tags.
        :type defaults: dict
        :return: A new model class with defaults applied.
        :rtype: type[RDFModel]
        """
        tagless_default_keys = self.untag_defaults(defaults, self.langtags)
        new_fields = {}
        for f_name, f_info in model_cls.model_fields.items():
            # check if no default value is set in parent class: This could also be removed so that all defaults are reset.
            if (
                type(getattr(f_info, "default")) is PydanticUndefinedType
                or getattr(f_info, "default") is None
            ):
                # check if property name is written in the default_values, the reverse check if a property has no value assigned could also work and would show all available properties for classes
                if f_name in tagless_default_keys:
                    # Check what datatype the property default value should be
                    if (
                        getattr(f_info, "json_schema_extra")["rdf_type"]
                        == "rdfs_literal"
                    ):
                        setattr(
                            f_info,
                            "default",
                            self.lang_literals(pd.Series(data=defaults), f_name),
                        )
                    elif getattr(f_info, "json_schema_extra")["rdf_type"] == "uri":
                        setattr(f_info, "default", AnyUrl(defaults[f_name]))
                    else:
                        print(f"{f_name} has a different datatype")
            new_fields[f_name] = Annotated[
                getattr(f_info, "annotation") | None,
                *getattr(f_info, "metadata"),
                Field(**{attr: getattr(f_info, attr) for attr in _Attrs}),
            ]  # , None <- add this to set all defaults to None for the fields
        return create_model(
            f"{model_cls.__name__}Optional",
            __base__=model_cls,
            **new_fields,
        )

    def create_catalog_model(self):
        if self._catalog_model is None:
            self._catalog_model = self.set_defaults(
                HRICatalog, self.default_values.get("catalog", {})
            )
        return self._catalog_model

    def create_dataset_model(self):
        if self._dataset_model is None:
            self._dataset_model = self.set_defaults(
                HRIDataset, self.default_values.get("dataset", {})
            )
        return self._dataset_model

    def create_agent_model(self):
        if self._agent_model is None:
            # For agents, use publisher defaults as base
            self._agent_model = self.set_defaults(
                HRIAgent, self.default_values.get("publisher", {})
            )
        return self._agent_model

    def create_vcard_model(self):
        if self._vcard_model is None:
            self._vcard_model = self.set_defaults(
                HRIVCard, self.default_values.get("contactPoint", {})
            )
        return self._vcard_model

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
        vcard_cls = self.create_vcard_model()
        vcard = vcard_cls(
            hasEmail="mailto:" + metadata.loc[self.model_config[prefix]["email"]],
            formatted_name=self.lang_literals(
                metadata, self.model_config[prefix]["name"]
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
        agent_cls = self.create_agent_model()
        return agent_cls(
            name=self.lang_literals(metadata, self.model_config[agent_prefix]["name"]),
            identifier=[metadata.loc[self.model_config[agent_prefix]["identifier"]]],
            homepage=URIRef(metadata.loc[self.model_config[agent_prefix]["homepage"]]),
            mbox="mailto:" + metadata.loc[self.model_config[agent_prefix]["mbox"]],
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
        catalog_cls = self.create_catalog_model()
        catalog = catalog_cls(
            title=self.lang_literals(metadata, self.model_config["title"]),
            description=self.lang_literals(metadata, self.model_config["description"]),
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
        dataset_cls = self.create_dataset_model()
        dataset = dataset_cls(
            title=self.lang_literals(metadata, self.model_config["title"]),
            description=self.lang_literals(metadata, self.model_config["description"]),
            # release_date=parser.isoparse("2024-07-01T11:11:11Z"),
            identifier=str(metadata.loc[self.model_config["identifier"]]),
            # modification_date=parser.isoparse("2024-06-04T13:36:10Z"),
            contact_point=contact_point,
            creator=creators,
            publisher=publisher,
            theme=[
                URIRef(
                    "http://publications.europa.eu/resource/authority/data-theme/"
                    + metadata.loc[self.model_config["theme"]]
                )
            ],
            access_rights=URIRef(
                "http://publications.europa.eu/resource/authority/access-right/"
                + str(metadata.loc[self.model_config["accessRights"]])
            ),
            keyword=metadata.loc[self.model_config["keywords"]].split(
                ","
            ),  # HACK: assumes the keywords are stored as a comma seperated list
            applicable_legislation=[
                URIRef(metadata.loc[self.model_config["applicableLegislation"]])
            ],
            number_of_records=LiteralField(
                value=str(metadata.loc[self.model_config["numberOfRecords"]]),
                datatype=XSD.nonNegativeInteger,
            ),  # relevant in current samplenavigator usecase
            number_of_unique_individuals=LiteralField(
                value=str(metadata.loc[self.model_config["numberOfUniqueIndividuals"]]),
                datatype=XSD.nonNegativeInteger,
            ),  # relevant in current samplenavigator usecase
            distribution=[],  # not sure if this is ever needed, as a new distribution is automatically linked to it's dataset by the FDP
        )
        return dataset
