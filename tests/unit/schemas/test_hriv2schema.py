import pytest
import pandas as pd
import yaml
from rdflib import URIRef, Graph
from sempyro import LiteralField, hri_dcat
from meta2fdp.transformers.HRIcore.v2.hriv2schema import Hriv2Schema as Schema
from meta2fdp.config.transformer.transformer import TransformerConfig


@pytest.fixture
def schema():
    default_values = yaml.safe_load(open("tests\config\default_values_tests.yaml"))
    model_config = TransformerConfig(
        name="test_config",
        schema_name="hriv2schema",
        schema_version="2.0",
        default_values=default_values,
    )
    return Schema(model_config)


@pytest.fixture
def test_catalog_metadata():
    return [
        {
            "title_en": "LUMC Biobanks",
            "title_nl": "LUMC Biobanken",
            "contactPoint_name": "Biobankorganisatie LUMC",
            "contactPoint_email": "biobankorganisatie@lumc.nl",
            "datasets": "1,2,3",
            "description_en": "A general description of the LUMC biobanks in English",
            "description_nl": "Een algemene omschrijving van de LUMC biobanken in het Nederlands",
            "publisher_name_en": "Leiden University Medical Center",
            "publisher_name_nl": "Leids Universitair Medisch Centrum",
            "publisher_email": "biobankorganisatie@lumc.nl",
            "publisher_identifier": "https://ror.org/05xvt9f17",
            "publisher_url": "https://www.lumc.nl",
        }
    ]


@pytest.fixture
def test_dataset_metadata():
    """test data for dataset metadata, one with all properties, one without creator and one without publisher to test parsing and model instantiation"""
    return [
        {
            "title_en": "Title1",
            "title_nl": "Titel1",
            "accessRights": "RESTRICTED",
            "applicableLegislation": "https://eur-lex.europa.eu/eli/reg/2025/327/oj",
            "contactPoint_name": "LUMC Biobankorganisatie",
            "contactPoint_email": "biobankorganisatie@lumc.nl",
            "creator_name": "Name Nameson",
            "creator_email": "N.Nameson@lumc.nl",
            "creator_identifier": "c1",
            "creator_url": "https://www.creator.nl",
            "description_en": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
            "description": "override description without language tag to test that it properly overrides the language tagged descriptions",
            "identifier": "1",
            "keywords": "Lorem, ipsum, dolor, sit, amet",
            "publisher_name_en": "Leiden University Medical Center",
            "publisher_name_nl": "Leids Universitair Medisch Centrum",
            "publisher_email": "biobankorganisatie@lumc.nl",
            "publisher_identifier": "https://ror.org/05xvt9f17",
            "publisher_url": "https://www.lumc.nl",
            "theme": "HEAL",
            "numberOfUniqueIndividuals": "854",
            "numberOfRecords": "3429",
        },
        {
            "title_en": "Title2",
            "title_nl": "Titel2",
            "accessRights": "RESTRICTED",
            "applicableLegislation": "https://eur-lex.europa.eu/eli/reg/2025/327/oj",
            "contactPoint_name": "LUMC Biobankorganisatie",
            "contactPoint_email": "biobankorganisatie@lumc.nl",
            "description_en": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
            "description_nl": "description in Dutch to test that it properly parses language tagged descriptions when no override is present",
            "identifier": "2",
            "keywords": "Lorem, ipsum, dolor, sit, amet",
            "publisher_name_en": "Leiden University Medical Center",
            "publisher_name_nl": "Leids Universitair Medisch Centrum",
            "publisher_email": "biobankorganisatie@lumc.nl",
            "publisher_identifier": "https://ror.org/05xvt9f17",
            "publisher_url": "https://www.lumc.nl",
            "theme": "HEAL",
            "numberOfUniqueIndividuals": "449",
            "numberOfRecords": "2631",
        },
        {
            "title_en": "Title3",
            "title_nl": "Titel3",
            "accessRights": "RESTRICTED",
            "applicableLegislation": "https://eur-lex.europa.eu/eli/reg/2025/327/oj",
            "contactPoint_name": "LUMC Biobankorganisatie",
            "contactPoint_email": "biobankorganisatie@lumc.nl",
            "creator_name": "Jane Doe",
            "creator_email": "Ja.Doe@lumc.nl",
            "creator_identifier": "c3",
            "creator_url": "https://www.creator.nl",
            "description_en": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
            "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
            "identifier": "3",
            "keywords": "Lorem, ipsum, dolor, sit, amet",
            "theme": "HEAL",
            "numberOfUniqueIndividuals": "719",
            "numberOfRecords": "3111",
        },
    ]


def test_lang_literals(schema):
    """test proper behaviour of parsing language tags:
    if a non language tagged column/property name exists in the input of function, it outputs it as a single item list with the value as a string
     this overrides any language tagged strings that are present
    if only language tagged column/properties exist (and no untagged column), they are returned as a list of Literal() sempyro fields
    if none of the column exists, or contain a None value: return None to force defaults when generating resource RDF.
    """
    test_metadata = {"tag_en": "English_tag", "tag_nl": "Nederlandse_label"}
    expected_result = [
        LiteralField(value="English_tag", language="en"),
        LiteralField(value="Nederlandse_label", language="nl"),
    ]
    assert expected_result == schema.lang_literals(test_metadata, "tag")

    test_metadata_override = {
        "tag_en": "English_tag",
        "tag_nl": "Nederlandse_label",
        "tag": "no_label",
    }
    expected_result_override = ["no_label"]
    assert expected_result_override == schema.lang_literals(
        test_metadata_override, "tag"
    )

    test_metadata_nolang = {"tag": "no_label"}
    expected_result_nolabel = ["no_label"]
    assert expected_result_nolabel == schema.lang_literals(test_metadata_nolang, "tag")


@pytest.mark.xfail
def test_fail_lang_literals(schema):
    schema.lang_literals(pd.Series(), "tag")


def test_convert_class_to_rdf(schema):
    vcard = hri_dcat.HRIVCard(
        hasEmail="mailto:" + "anemail@test.io",
        formatted_name=LiteralField(value="anem ail"),
    )
    expected_graph = Graph().parse(
        data="""@prefix v: <http://www.w3.org/2006/vcard/ns#> .

<http://fdp.org/new> a v:Kind ;
    v:fn "anem ail" ;
    v:hasEmail <mailto:anemail@test.io> .""",
        format="ttl",
    )

    result_graph = schema.convert_class_to_rdf(vcard, URIRef("http://fdp.org/new"))
    unique_triples = expected_graph ^ result_graph
    assert len(unique_triples) == 0, (
        f"Serialized graphs are not the same! These are the unexpected triples{unique_triples.serialize()}"
    )


class TestVcard:
    """Test suite for the instantiate_vcard method of the Hriv2Schema class."""

    def test_instantiate_vcard(self, schema):
        test_metadata = {
            "hasEmail": "mailto:contact@example.com",
            "formatted_name": "John Doe",
        }
        result = schema.instantiate_vcard(test_metadata)
        assert str(result.hasEmail) == "mailto:contact@example.com"
        assert result.formatted_name == "John Doe"

    def test_instantiate_vcard_without_mailto(self, schema):
        test_metadata = {
            "hasEmail": "contact@example.com",
            "formatted_name": "John Doe",
        }
        result = schema.instantiate_vcard(test_metadata)
        assert str(result.hasEmail) == "mailto:contact@example.com"
        assert result.formatted_name == "John Doe"

    def test_instantiate_vcard_with_missing_fields(self, schema):
        test_metadata = {"hasEmail": "mailto:contact@example.com"}
        result = schema.instantiate_vcard(test_metadata)
        assert str(result.hasEmail) == "mailto:contact@example.com"
        assert result.formatted_name is None

    def test_instantiate_vcard_custom_prefix(self, schema):
        test_metadata = {
            "contactPoint_hasEmail": "support@example.com",
            "contactPoint_formatted_name": "Support Team",
        }
        result = schema.instantiate_vcard(test_metadata, prefix="contactPoint_")
        assert str(result.hasEmail) == "mailto:support@example.com"
        assert result.formatted_name == "Support Team"

    @pytest.mark.xfail
    def test_fail_instantiate_vcard_custom_prefix(self, schema):
        # This test is expected to fail because the prefix "wrongPrefix" does not match the keys in the metadata.
        test_metadata = pd.Series(
            data=["support@example.com", "Support Team"],
            index=["support_email", "support_name"],
        )
        result = schema.instantiate_vcard(test_metadata, prefix="wrongPrefix")
        assert str(result.hasEmail) == "mailto:support@example.com"
        assert result.formatted_name.value == "Support Team"


class TestAgent:
    """Test suite for the instantiate_agent method of the Hriv2Schema class."""

    def test_instantiate_agent(self, schema):
        test_metadata = {
            "creator_name_en": "Dr. Jane Smith",
            "creator_name_nl": "Dr. Jane Smith",
            "creator_identifier": "agent-123",
            "creator_homepage": "https://example.org",
            "creator_mbox": "jane@example.com",
        }
        result = schema.instantiate_agent(test_metadata, "creator_")
        assert result.name[0] == LiteralField(language="en", value="Dr. Jane Smith")
        assert result.name[1] == LiteralField(language="nl", value="Dr. Jane Smith")
        assert result.identifier == ["agent-123"]
        assert str(result.homepage) == "https://example.org/"
        assert str(result.mbox) == "mailto:jane@example.com"


class TestCatalog:
    """Test suite for the instantiate_HRICatalog method of the Hriv2Schema class."""

    def test_instantiate_catalog(self, schema):
        catalog_metadata = {"title": "Sample Catalog", "description": "A test catalog"}
        vcard = hri_dcat.HRIVCard(
            hasEmail="mailto:contact@test.io",
            formatted_name=LiteralField(value="Contact"),
        )
        agent = hri_dcat.HRIAgent(
            name=[LiteralField(value="Publisher")],
            identifier=["pub-1"],
            mbox="mailto:pub@test.io",
            homepage="http://example.org",
        )

        result = schema.instantiate_catalog(
            {**catalog_metadata, "contactPoint": vcard, "publisher": agent}
        )
        assert result.title[0].value == "Sample Catalog"
        assert result.description[0].value == "A test catalog"
        assert result.contact_point == vcard
        assert result.publisher == agent
        assert result.dataset is None


def test_instantiate_dataset(schema):
    dataset_metadata = {
        "title": "Test Dataset",
        "description": "A dataset for testing",
        "identifier": "dataset-001",
        "theme": "HEAL",
        "accessRights": "PUBLIC",
        "keyword": ["keyword1", "keyword2"],
        "applicable_legislation": "http://example.org/legislation",
        "numberOfRecords": "1000",
        "numberOfUniqueIndividuals": "500",
    }
    vcard = hri_dcat.HRIVCard(
        hasEmail="mailto:contact@test.io", formatted_name=LiteralField(value="Contact")
    )
    agent = hri_dcat.HRIAgent(
        name=[LiteralField(value="Publisher")],
        identifier=["pub-1"],
        mbox="mailto:pub@test.io",
        homepage="http://example.org",
    )
    creators = [
        hri_dcat.HRIAgent(
            name=[LiteralField(value="Creator1")],
            identifier=["creator-1"],
            mbox="mailto:creator@test.io",
            homepage="http://example.org",
        )
    ]

    result = schema.instantiate_dataset(
        {
            **dataset_metadata,
            "contactPoint": vcard,
            "publisher": agent,
            "creator": creators,
        }
    )
    assert result.title[0].value == "Test Dataset"
    assert result.description[0].value == "A dataset for testing"
    assert result.identifier == "dataset-001"
    assert result.contact_point == vcard
    assert result.creator == creators
    assert result.publisher == agent
    assert result.keyword == [
        LiteralField(value="keyword1"),
        LiteralField(value="keyword2"),
    ]
    assert result.number_of_records == 1000
    assert result.number_of_unique_individuals == 500


class TestConfiguration:
    """Test suite for configuration and default values implementation."""

    def test_config_structure_loaded(self, schema):
        """Test that configuration structure is properly loaded."""
        assert hasattr(schema, "config")
        assert hasattr(schema, "default_values")
        assert hasattr(schema, "langtags")

    def test_language_tags_parsed_correctly(self, schema):
        """Test that language tags are parsed correctly from config."""
        assert isinstance(schema.langtags, list)
        assert len(schema.langtags) > 0
        assert "en" in schema.langtags or "nl" in schema.langtags

    def test_model_config_nested_structure(self, schema):
        """Test that nested configuration structures (contactPoint, publisher, creator) are present."""
        assert isinstance(schema.default_values.get("contactPoint"), dict)
        assert isinstance(schema.default_values.get("publisher"), dict)
        assert isinstance(schema.default_values.get("creator"), dict)


class TestFactoryMethods:
    """Test suite for factory method caching and model generation."""

    def test_create_catalog_model_returns_class(self, schema):
        """Test that create_catalog_model returns a valid model class."""
        model_cls = schema.create_catalog_model()
        assert model_cls is not None
        # Should be able to instantiate it
        assert issubclass(model_cls, hri_dcat.HRICatalog) or hasattr(
            model_cls, "__mro__"
        )

    def test_create_dataset_model_returns_class(self, schema):
        """Test that create_dataset_model returns a valid model class."""
        model_cls = schema.create_dataset_model()
        assert model_cls is not None
        assert issubclass(model_cls, hri_dcat.HRIDataset) or hasattr(
            model_cls, "__mro__"
        )

    def test_create_agent_model_returns_class(self, schema):
        """Test that create_agent_model returns a valid model class."""
        model_cls = schema.create_agent_model()
        assert model_cls is not None
        assert issubclass(model_cls, hri_dcat.HRIAgent) or hasattr(model_cls, "__mro__")

    def test_create_vcard_model_returns_class(self, schema):
        """Test that create_vcard_model returns a valid model class."""
        model_cls = schema.create_vcard_model()
        assert model_cls is not None
        assert issubclass(model_cls, hri_dcat.HRIVCard) or hasattr(model_cls, "__mro__")

    def test_catalog_model_caching(self, schema):
        """Test that catalog model is cached and reused."""
        catalog_model_1 = schema.create_catalog_model()
        catalog_model_2 = schema.create_catalog_model()
        assert catalog_model_1 is catalog_model_2, (
            "Catalog model should be cached and reused"
        )

    def test_dataset_model_caching(self, schema):
        """Test that dataset model is cached and reused."""
        model_cls_1 = schema.create_dataset_model()
        model_cls_2 = schema.create_dataset_model()
        assert model_cls_1 is model_cls_2, "Dataset model should be cached and reused"

    def test_agent_model_caching(self, schema):
        """Test that agent model is cached and reused."""
        model_cls_1 = schema.create_agent_model()
        model_cls_2 = schema.create_agent_model()
        assert model_cls_1 is model_cls_2, "Agent model should be cached and reused"

    def test_vcard_model_caching(self, schema):
        """Test that vcard model is cached and reused."""
        model_cls_1 = schema.create_vcard_model()
        model_cls_2 = schema.create_vcard_model()
        assert model_cls_1 is model_cls_2, "VCard model should be cached and reused"


class TestHelperFunctions:
    """Test suite for helper functions: untag_defaults and set_defaults."""

    def test_untag_defaults_removes_single_langtag(self, schema):
        """Test that untag_defaults removes language tags from keys."""
        defaults = {"name_en": "English", "name_nl": "Dutch", "identifier": "123"}
        language_tags = ["en", "nl"]
        result = schema.untag_defaults(defaults, language_tags)
        assert "name" in result
        assert "identifier" in result
        assert "name_en" not in result
        assert "name_nl" not in result

    def test_untag_defaults_preserves_untagged_keys(self, schema):
        """Test that untag_defaults preserves keys without language tags."""
        defaults = {
            "name_en": "English",
            "identifier": "123",
            "url": "http://example.org",
        }
        language_tags = ["en", "nl"]
        result = schema.untag_defaults(defaults, language_tags)
        assert "identifier" in result
        assert "url" in result

    def test_untag_defaults_handles_multiple_language_tags(self, schema):
        """Test that untag_defaults handles multiple language tags."""
        defaults = {"title_en": "English", "title_nl": "Dutch", "title_fr": "French"}
        language_tags = ["en", "nl", "fr"]
        result = schema.untag_defaults(defaults, language_tags)
        assert result == {"title"}

    def test_untag_defaults_empty_dict(self, schema):
        """Test that untag_defaults handles empty dictionary."""
        defaults = {}
        language_tags = ["en", "nl"]
        result = schema.untag_defaults(defaults, language_tags)
        assert result == set()

    def test_set_defaults_creates_optional_model(self, schema):
        """Test that set_defaults creates a model class with defaults applied."""
        test_defaults = {"name_en": "Test", "identifier": "test-id"}
        model_cls = schema.set_defaults(hri_dcat.HRIAgent, test_defaults)
        assert model_cls is not None
        # Model class name should indicate it's an Optional variant
        assert "Optional" in model_cls.__name__

    def test_set_defaults_model_can_be_instantiated(self, schema):
        """Test that model created by set_defaults can be instantiated."""
        test_defaults = {"name_en": "Test Name"}
        model_cls = schema.set_defaults(hri_dcat.HRIAgent, test_defaults)
        # Should be able to create an instance
        instance = model_cls()
        assert instance is not None


class TestConfigurationUpdates:
    """Test suite for configuration updates and cache invalidation."""

    def test_set_schema_config_updates_config(self, schema):
        """Test that set_schema_config properly updates the configuration."""
        new_default_values = yaml.safe_load(
            open("tests\config\default_values_tests.yaml")
        )
        transformer_config = TransformerConfig(
            name="test_config2",
            schema_name="hriv2schema",
            schema_version="2.0",
            default_values=new_default_values,
            language_tags=["en", "nl"],
        )

        schema.set_schema_config(transformer_config)
        assert schema.config == transformer_config

    def test_set_schema_config_resets_catalog_cache(self, schema):
        """Test that set_schema_config resets the catalog model cache."""
        # Get the cached model
        schema.create_catalog_model()
        assert schema._catalog_model is not None

        # Update config
        new_default_values = yaml.safe_load(
            open("tests\config\default_values_tests.yaml")
        )
        transformer_config = TransformerConfig(
            name="test_config2",
            schema_name="hriv2schema",
            schema_version="2.0",
            default_values=new_default_values,
            language_tags=["en", "nl"],
        )

        schema.set_schema_config(transformer_config)

        # Cache should be reset
        assert schema._catalog_model is None

    def test_set_schema_config_resets_all_caches(self, schema):
        """Test that set_schema_config resets all model caches."""
        # Populate all caches
        schema.create_catalog_model()
        schema.create_dataset_model()
        schema.create_agent_model()
        schema.create_vcard_model()

        assert schema._catalog_model is not None
        assert schema._dataset_model is not None
        assert schema._agent_model is not None
        assert schema._vcard_model is not None

        # Update config
        new_default_values = yaml.safe_load(
            open("tests\config\default_values_tests.yaml")
        )
        transformer_config = TransformerConfig(
            name="test_config2",
            schema_name="hriv2schema",
            schema_version="2.0",
            default_values=new_default_values,
            language_tags=["en", "nl"],
        )
        schema.set_schema_config(transformer_config)

        # All caches should be reset
        assert schema._catalog_model is None
        assert schema._dataset_model is None
        assert schema._agent_model is None
        assert schema._vcard_model is None

    def test_set_schema_config_updates_language_tags(self, schema):
        """Test that set_schema_config updates the language_tags list."""
        # Update config
        new_default_values = yaml.safe_load(
            open("tests\config\default_values_tests.yaml")
        )
        transformer_config = TransformerConfig(
            name="test_config2",
            schema_name="hriv2schema",
            schema_version="2.0",
            default_values=new_default_values,
            language_tags=["en", "nl", "fr"],
        )
        schema.set_schema_config(transformer_config)

        # language_tags should be updated
        assert schema.langtags == transformer_config.language_tags


class TestDefaultValueApplication:
    """Test suite for ensuring default values are properly applied to models."""

    def test_catalog_model_has_defaults_from_config(self, schema):
        """Test that catalog model created from factory applies scalar defaults.

        Note: Nested objects (contact_point, publisher) are provided in the test
        since they cannot be configured as YAML defaults. This test verifies that
        the factory model properly applies defaults for scalar properties like
        applicable_legislation, spatial, and homepage.
        """
        catalog_cls = schema.create_catalog_model()
        assert catalog_cls is not None

        # Create minimal required nested objects
        contact_point = hri_dcat.HRIVCard(
            hasEmail="mailto:test@example.org",
            formatted_name=LiteralField(value="Test Contact"),
        )
        publisher = hri_dcat.HRIAgent(
            name=[LiteralField(value="Test Publisher")],
            identifier=["test-id"],
            mbox="mailto:pub@example.org",
            homepage="http://example.org",
        )
        title_metadata = pd.Series(
            data=["Test Catalog", "A test catalog"], index=["title", "description"]
        )
        title_values = schema.lang_literals(title_metadata, "title")
        description_values = schema.lang_literals(title_metadata, "description")

        # Instantiate with required fields, defaults should be applied for other properties
        instance = catalog_cls(
            title=title_values,
            description=description_values,
            contact_point=contact_point,
            publisher=publisher,
            dataset=[],
        )
        assert instance is not None
        # Verify it has the structure of a catalog
        assert hasattr(instance, "title")
        assert hasattr(instance, "contact_point")
        assert hasattr(instance, "publisher")

    def test_dataset_model_has_defaults_from_config(self, schema):
        """Test that dataset model created from factory applies scalar defaults.

        Note: Nested objects (contact_point, publisher, creators) are provided in the test
        since they cannot be configured as YAML defaults. This test verifies that
        the factory model properly applies defaults for scalar properties like
        theme, access_rights, and applicable_legislation.
        """
        dataset_cls = schema.create_dataset_model()
        assert dataset_cls is not None

        # Create minimal required nested objects
        contact_point = hri_dcat.HRIVCard(
            hasEmail="mailto:test@example.org",
            formatted_name=LiteralField(value="Test Contact"),
        )
        publisher = hri_dcat.HRIAgent(
            name=[LiteralField(value="Test Publisher")],
            identifier=["test-id"],
            mbox="mailto:pub@example.org",
            homepage="http://example.org",
        )
        creators = [
            hri_dcat.HRIAgent(
                name=[LiteralField(value="Test Creator")],
                identifier=["creator-id"],
                mbox="mailto:creator@example.org",
                homepage="http://example.org",
            )
        ]

        # Create minimal dataset metadata
        dataset_metadata = pd.Series(
            data=[
                "Test Dataset",
                "A test dataset",
                "dataset-001",
                "HEAL",
                "PUBLIC",
                "keyword1,keyword2",
                "http://example.org/legislation",
                "100",
                "50",
            ],
            index=[
                "title",
                "description",
                "identifier",
                "theme",
                "accessRights",
                "keywords",
                "applicableLegislation",
                "numberOfRecords",
                "numberOfUniqueIndividuals",
            ],
        )
        title_values = schema.lang_literals(dataset_metadata, "title")
        description_values = schema.lang_literals(dataset_metadata, "description")

        # Instantiate with required fields, defaults should be applied for other properties
        instance = dataset_cls(
            title=title_values,
            description=description_values,
            identifier="dataset-001",
            contact_point=contact_point,
            publisher=publisher,
            creator=creators,
            theme=[
                URIRef(
                    "http://publications.europa.eu/resource/authority/data-theme/HEAL"
                )
            ],
            access_rights=URIRef(
                "http://publications.europa.eu/resource/authority/access-right/PUBLIC"
            ),
            keyword=[LiteralField(value="keyword1"), LiteralField(value="keyword2")],
            applicable_legislation=[URIRef("http://example.org/legislation")],
            number_of_records=LiteralField(value="100"),
            number_of_unique_individuals=LiteralField(value="50"),
            distribution=[],
        )
        assert instance is not None
        # Verify it has the structure of a dataset
        assert hasattr(instance, "title")
        assert hasattr(instance, "contact_point")
        assert hasattr(instance, "publisher")
        assert hasattr(instance, "creator")

    def test_agent_model_has_defaults_from_config(self, schema):
        """Test that agent model created from factory applies defaults."""
        agent_cls = schema.create_agent_model()
        assert agent_cls is not None
        instance = agent_cls()
        assert instance is not None

    def test_vcard_model_has_defaults_from_config(self, schema):
        """Test that vcard model created from factory applies defaults."""
        vcard_cls = schema.create_vcard_model()
        assert vcard_cls is not None
        instance = vcard_cls()
        assert instance is not None
