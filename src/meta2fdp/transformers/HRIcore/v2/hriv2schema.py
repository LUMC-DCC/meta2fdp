"""This module contains the implementation of the HRIV2Schema class, which is a specific schema for converting metadata into RDF format using the SeMPyRO library. The class provides methods for instantiating various SeMPyRO classes such as HRICatalog, HRIDataset, HRIVCard, and HRIAgent based on the provided metadata. It also includes a method for converting these classes into RDF graphs. The schema configuration can be set and updated as needed."""

import logging

import pandas as pd
from rdflib import Graph, URIRef
from sempyro.dcat import DCATResource
from meta2fdp.transformers.base import AbstractSchema
from meta2fdp.config.transformer.transformer import TransformerConfig
from sempyro import LiteralField
from sempyro.hri_dcat import (
    HRICatalog,
    HRIDataset,
    HRIVCard,
    HRIAgent,
)
from sempyro import RDFModel
from typing import Annotated
from pydantic import Field, create_model, AnyUrl, model_validator
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


@model_validator(mode="before")
def replace_nones_with_defaults(cls, values):

    if not isinstance(values, dict):
        return values

    for name, field in cls.model_fields.items():
        if values.get(name) is None:
            if field.default_factory is not None:
                logging.debug(f"Setting default for {name} using default_factory")
                values[name] = field.default_factory()
            elif (
                field.default is not None
                and type(field.default) is not PydanticUndefinedType
            ):
                logging.debug(f"Setting default for {name}: {field.default}")
                logging.debug(f"default is of type:{type(field.default)}")
                values[name] = field.default

    return values


class Hriv2Schema(AbstractSchema):
    def __init__(self, config: TransformerConfig) -> None:
        self.config = config

        # Assume a TransformerConfig-like object
        self.default_values = getattr(config, "default_values", {}) or {}
        self.langtags = (
            getattr(config, "language_tags", ["en"])
            if hasattr(config, "language_tags")
            else ["en"]
        )
        logging.debug(f"Initialized Hriv2Schema with config: {config}")
        logging.debug(
            f"Default values catalog: \n {self.default_values.get('catalog', {})}"
        )
        logging.debug(
            f"Default values dataset: \n {self.default_values.get('dataset', {})}"
        )
        logging.debug(
            f"Default values publisher: \n {self.default_values.get('publisher', {})}"
        )
        logging.debug(
            f"Default values contactPoint: \n {self.default_values.get('contactPoint', {})}"
        )
        logging.debug(
            f"Default values creator: \n {self.default_values.get('creator', {})}"
        )
        logging.debug(f"Language tags: {self.langtags}")

        # Cache factory-generated model classes
        self._catalog_model = None
        self._dataset_model = None
        self._agent_model = None
        self._vcard_model = None

    def set_schema_config(self, config: dict) -> None:
        self.config = config

        # Assume a TransformerConfig-like object
        self.default_values = getattr(config, "default_values", {}) or {}
        self.langtags = (
            getattr(config, "language_tags", ["en"])
            if hasattr(config, "language_tags")
            else ["en"]
        )
        logging.debug(f"Updated Hriv2Schema with config: {config}")
        logging.debug(f"Updated default values: {self.default_values}")
        logging.debug(f"Updated language tags: {self.langtags}")

        # Reset cached models if config changes
        self._catalog_model = None
        self._dataset_model = None
        self._agent_model = None
        self._vcard_model = None

    def convert_class_to_rdf(self, HRIresource: DCATResource, uri: URIRef) -> Graph:
        return HRIresource.to_graph(uri)

    def listed_properties(self, metadata: dict, colname: str) -> list | None:
        content = metadata.get(colname, None)
        if content is not None and not isinstance(content, list):
            return [content]
        else:
            return content

    def theme_properties(self, metadata: dict, colname: str) -> list[URIRef] | None:
        themes = self.listed_properties(metadata, colname)
        if themes is not None:
            return [
                URIRef(theme)
                if theme.startswith("http")
                else URIRef(
                    "http://publications.europa.eu/resource/authority/data-theme/"
                    + theme
                )
                for theme in themes
            ]
        else:
            return None

    def access_rights_properties(
        self, metadata: dict, colname: str
    ) -> list[URIRef] | None:
        access_rights = metadata.get(colname, None)
        if access_rights is not None:
            return (
                URIRef(access_rights)
                if access_rights.startswith("http")
                else URIRef(
                    "http://publications.europa.eu/resource/authority/access-right/"
                    + access_rights
                )
            )
        else:
            return None

    def lang_literals(self, metadata: dict, colname: str) -> list[LiteralField] | None:
        """Create LiteralField objects from metadata, handling language tags.

        This function attempts to create LiteralField objects for a given column name
        from the metadata series. It first checks for a non-language-tagged value,
        then if no such value is found, looks for language-tagged variants based on configured language tags in the schema.

        :param metadata: Metadata series containing resource properties.
        :type metadata: pd.Series
        :param colname: Base column name for the literal property.
        :type colname: str
        :return: List of LiteralField objects, each with appropriate language tag if applicable.
        :rtype: list[LiteralField]
        :raises Warning: If no matching property (tagged or untagged) is found in the metadata.
        """
        properties = []
        if colname in metadata.keys():
            # check if the property is a list and not empty, return it as is
            if isinstance(metadata[colname], list):
                if len(metadata[colname]) == 0:
                    return None
                return metadata[colname]
            if not pd.isna(metadata[colname]) or metadata[colname] is not None:
                nolang_literal = metadata[colname]
                properties.append(nolang_literal)
        else:
            for langtag in self.langtags:
                property_colname = colname + "_" + langtag
                if property_colname in metadata.keys():
                    if isinstance(metadata[property_colname], list):
                        if len(metadata[property_colname]) == 0:
                            return None
                        for property in metadata[property_colname]:
                            properties.append(
                                LiteralField(value=property, language=langtag)
                            )
                    elif (
                        not pd.isna(metadata[property_colname])
                        or metadata[property_colname] is not None
                    ):
                        langtagged_literal = LiteralField(
                            value=metadata[property_colname], language=langtag
                        )
                        logging.debug(
                            f"found following langtagged_literal: {langtagged_literal}"
                        )
                        properties.append(langtagged_literal)
        if len(properties) == 0:
            return None
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
            ]

        logging.debug(f"Creating model with defaults for {model_cls.__name__}")
        # logging.debug(f"New fields: {new_fields}")
        model_with_defaults = create_model(
            f"{model_cls.__name__}",
            __base__=model_cls,
            __validators__={
                "replace_nones": replace_nones_with_defaults,
            },
            **new_fields,
        )
        return model_with_defaults

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

    def instantiate_vcard(self, vcard_metadata: dict, prefix="") -> HRIVCard:
        """Modified instantiation of HRIVcard that has the recommended values
        removed.

        :param metadata: A Series containing metadata about a contact point
        :type metadata: Series
        :param prefix: the prefix of the column names associated to contactpoint, defaults to "contactPoint"
        :type prefix: str, optional
        :return: A HRIVcard pydantic class
        :rtype: HRIVCard
        """
        logging.debug(
            f"Instantiating vCard with metadata: {vcard_metadata} and prefix: {prefix}"
        )
        kwargs = {
            "formatted_name": vcard_metadata.get(prefix + "formatted_name", None),
            "hasEmail": vcard_metadata.get(prefix + "hasEmail", None),
            "contact_page": self.listed_properties(
                vcard_metadata, prefix + "contact_page"
            ),
        }
        vcard_cls = self.create_vcard_model()
        logging.debug(vcard_cls.model_fields)
        logging.debug(kwargs)
        vcard = vcard_cls(**kwargs)
        return vcard

    def instantiate_agent(self, agent_metadata: dict, prefix="") -> HRIAgent:
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
        logging.debug(
            f"Instantiating agent with metadata: {agent_metadata} and prefix: {prefix}"
        )
        kwargs = {
            "name": self.lang_literals(agent_metadata, prefix + "name"),
            "identifier": self.listed_properties(agent_metadata, prefix + "identifier"),
            "mbox": agent_metadata.get(prefix + "mbox", None),
            "homepage": agent_metadata.get(prefix + "homepage", None),
            "spatial": self.listed_properties(agent_metadata, prefix + "spatial"),
            "publisher_note": agent_metadata.get(prefix + "publisher_note", None),
            "publisher_type": agent_metadata.get(prefix + "publisher_type", None),
            "type": agent_metadata.get(prefix + "type", None),
        }
        logging.debug(f"Instantiating agent with kwargs: {kwargs}")
        agent_cls = self.create_agent_model()
        logging.debug(f"Agent model fields: {agent_cls.model_fields}")
        return agent_cls(**kwargs)

    def qualifiedattribution_graph(
        self, attribution_metadata: pd.Series, prefix="auth1"
    ) -> Graph:
        QualifiedAttribution = self.instantiate_agent(attribution_metadata, prefix)
        # somehow add Role to the agent

        return QualifiedAttribution

    def instantiate_catalog(
        self, metadata: dict, creators=None, publisher=None, contact_point=None
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
        logging.debug(f"Instantiating catalog with metadata: {metadata}")
        kwargs = {
            "title": self.lang_literals(metadata, "title"),
            "description": self.lang_literals(metadata, "description"),
            "dataset": metadata.get("dataset", None),
            "service": metadata.get("service", None),
            "catalog": metadata.get("catalog", None),
            "applicable_legislation": self.listed_properties(
                metadata, "applicable_legislation"
            ),
            "has_part": metadata.get("has_part", None),
            "homepage": metadata.get("homepage", None),
            "theme": self.theme_properties(metadata, "theme"),
            "keyword": self.lang_literals(metadata, "keyword"),
            "license": metadata.get("license", None),
        }
        logging.debug(f"Instantiating catalog with kwargs: {kwargs}")
        logging.debug(f"creator class type: {type(creators)}")
        logging.debug(f"publisher class type: {type(publisher)}")
        catalog_cls = self.create_catalog_model()
        logging.debug(f"Catalog model fields: {catalog_cls.model_fields}")
        catalog = catalog_cls(
            creator=creators, publisher=publisher, contact_point=contact_point, **kwargs
        )
        return catalog

    def instantiate_dataset(
        self, metadata: dict, creators=None, publisher=None, contact_point=None
    ) -> HRIDataset:
        """This a sempyro dataset constructor that tries to build a dataset resource description using
        the samplenavigator reference data as a default. See parent class for all possible options.

        :param metadata: The metadata of a dataset
        :type metadata: Series
        :param contact_point: A dataset has one contactpoint (for now) and is described with a Vcard
        :type contact_point: HRIVCard
        :param publisher: Publisher should be LUMC, see configuration for default values that could be used.
        :type publisher: HRIAgent
        :param creators: A dataset can have multiple creators, these are also described with Agents.
        :type creators: list[HRIAgent]
        :return: Dataset class for reuse or manipulation
        :rtype: HRIDataset
        """
        logging.debug(f"Instantiating dataset with metadata: {metadata}")
        kwargs = {
            "title": self.lang_literals(metadata, "title"),
            "description": self.lang_literals(metadata, "description"),
            "identifier": metadata.get("identifier", None),
            "theme": self.theme_properties(metadata, "theme"),
            "access_rights": self.access_rights_properties(metadata, "accessRights"),
            "keyword": self.lang_literals(metadata, "keyword"),
            "applicable_legislation": self.listed_properties(
                metadata, "applicable_legislation"
            ),
            "number_of_records": metadata.get("numberOfRecords", None),
            "number_of_unique_individuals": metadata.get(
                "numberOfUniqueIndividuals", None
            ),
            # add more properties as needed
        }

        dataset_cls = self.create_dataset_model()
        dataset = dataset_cls(
            creator=creators,
            publisher=publisher,
            contact_point=contact_point,
            **kwargs,
        )
        return dataset
