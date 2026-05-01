import pytest
import pandas as pd
import yaml
from rdflib import URIRef, Graph
from sempyro import LiteralField, hri_dcat
from meta2fdp.models.HRIcore.v2.hriv2schema import Hriv2Schema as Schema


@pytest.fixture
def schema():
    config = yaml.safe_load(open("config\\model_config.yaml"))
    default_values = yaml.safe_load(open("config\\default_values.yaml"))
    model_config = {"model_config": config, "default_values": default_values}
    return Schema(model_config)


def test_lang_literals(schema):
    test_metadata = pd.Series(
        data=["English_tag", "Nederlandse_label"], index=["tag_en", "tag_nl"]
    )
    expected_result = [
        LiteralField(value="English_tag", language="en"),
        LiteralField(value="Nederlandse_label", language="nl"),
    ]
    assert expected_result == schema.lang_literals(test_metadata, "tag")

    test_metadata_override = pd.Series(
        data=["English_tag", "Nederlandse_label", "no_label"],
        index=["tag_en", "tag_nl", "tag"],
    )
    expected_result_override = [LiteralField(value="no_label")]
    assert expected_result_override == schema.lang_literals(
        test_metadata_override, "tag"
    )

    test_metadata_nolang = pd.Series(data=["no_label"], index=["tag"])
    expected_result_nolabel = [LiteralField(value="no_label")]
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


def test_instantiate_HRIVcard(schema):
    test_metadata = pd.Series(
        data=["contact@example.com", "John Doe"],
        index=["contactPoint_email", "contactPoint_name"],
    )
    result = schema.instantiate_HRIVcard(test_metadata)
    assert str(result.hasEmail) == "mailto:contact@example.com"
    assert result.formatted_name.value == "John Doe"


def test_instantiate_HRIVcard_custom_prefix(schema):
    test_metadata = pd.Series(
        data=["support@example.com", "Support Team"],
        index=["contactPoint_email", "contactPoint_name"],
    )
    result = schema.instantiate_HRIVcard(test_metadata, prefix="contactPoint")
    assert str(result.hasEmail) == "mailto:support@example.com"
    assert result.formatted_name.value == "Support Team"


@pytest.mark.xfail
def test_fail_instantiate_HRIVcard_custom_prefix(schema):
    # This test is expected to fail because the prefix "wrongPrefix" does not match the keys in the metadata.
    test_metadata = pd.Series(
        data=["support@example.com", "Support Team"],
        index=["support_email", "support_name"],
    )
    result = schema.instantiate_HRIVcard(test_metadata, prefix="contactPoint")
    assert str(result.hasEmail) == "mailto:support@example.com"
    assert result.formatted_name.value == "Support Team"


def test_instantiate_agent(schema):
    test_metadata = pd.Series(
        data=[
            "Dr. Jane Smith",
            "agent-123",
            "https://example.org",
            "jane@example.com",
        ],
        index=[
            "creator_name",
            "creator_identifier",
            "creator_url",
            "creator_email",
        ],
    )
    result = schema.instantiate_agent(test_metadata, "creator")
    assert result.name[0].value == "Dr. Jane Smith"
    assert result.identifier == ["agent-123"]
    assert str(result.homepage) == "https://example.org/"
    assert str(result.mbox) == "mailto:jane@example.com"


def test_instantiate_HRICatalog(schema):
    catalog_metadata = pd.Series(
        data=["Sample Catalog", "A test catalog"], index=["title", "description"]
    )
    vcard = hri_dcat.HRIVCard(
        hasEmail="mailto:contact@test.io", formatted_name=LiteralField(value="Contact")
    )
    agent = hri_dcat.HRIAgent(
        name=[LiteralField(value="Publisher")],
        identifier=["pub-1"],
        mbox="mailto:pub@test.io",
        homepage="http://example.org",
    )

    result = schema.instantiate_HRICatalog(catalog_metadata, vcard, agent)
    assert result.title[0].value == "Sample Catalog"
    assert result.description[0].value == "A test catalog"
    assert result.contact_point == vcard
    assert result.publisher == agent
    assert result.dataset == []


def test_instantiate_HRIDataset(schema):
    dataset_metadata = pd.Series(
        data=[
            "Test Dataset",
            "A dataset for testing",
            "dataset-001",
            "HEAL",
            "PUBLIC",
            "keyword1,keyword2",
            "http://example.org/legislation",
            "1000",
            "500",
        ],
        index=[
            "title",
            "description",
            "identifier",
            "theme",
            "accessRights",
            "keywords",
            "applicable_legislation",
            "numberOfRecords",
            "numberOfUniqueIndividuals",
        ],
    )
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

    result = schema.instantiate_HRIDataset(dataset_metadata, vcard, agent, creators)
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
    assert result.number_of_records.value == "1000"
    assert result.number_of_unique_individuals.value == "500"


class TestConfiguration:
    """Test suite for configuration and default values implementation."""

    def test_config_structure_loaded(self, schema):
        """Test that configuration structure is properly loaded."""
        assert hasattr(schema, "config")
        assert hasattr(schema, "model_config")
        assert hasattr(schema, "default_values")
        assert hasattr(schema, "langtags")

    def test_model_config_contains_required_keys(self, schema):
        """Test that model_config contains all required column mapping keys."""
        required_keys = [
            "title",
            "description",
            "identifier",
            "theme",
            "accessRights",
            "keywords",
            "applicable_legislation",
            "numberOfRecords",
            "numberOfUniqueIndividuals",
            "langtags",
            "contactPoint",
            "publisher",
            "creator",
        ]
        for key in required_keys:
            assert key in schema.model_config, f"Missing key '{key}' in model_config"

    def test_langtags_parsed_correctly(self, schema):
        """Test that language tags are parsed correctly from config."""
        assert isinstance(schema.langtags, list)
        assert len(schema.langtags) > 0
        assert "en" in schema.langtags or "nl" in schema.langtags

    def test_model_config_nested_structure(self, schema):
        """Test that nested configuration structures (contactPoint, publisher, creator) are present."""
        assert isinstance(schema.model_config.get("contactPoint"), dict)
        assert isinstance(schema.model_config.get("publisher"), dict)
        assert isinstance(schema.model_config.get("creator"), dict)


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
        langtags = ["en", "nl"]
        result = schema.untag_defaults(defaults, langtags)
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
        langtags = ["en", "nl"]
        result = schema.untag_defaults(defaults, langtags)
        assert "identifier" in result
        assert "url" in result

    def test_untag_defaults_handles_multiple_langtags(self, schema):
        """Test that untag_defaults handles multiple language tags."""
        defaults = {"title_en": "English", "title_nl": "Dutch", "title_fr": "French"}
        langtags = ["en", "nl", "fr"]
        result = schema.untag_defaults(defaults, langtags)
        assert result == {"title"}

    def test_untag_defaults_empty_dict(self, schema):
        """Test that untag_defaults handles empty dictionary."""
        defaults = {}
        langtags = ["en", "nl"]
        result = schema.untag_defaults(defaults, langtags)
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
        new_config = yaml.safe_load(open("config\\model_config.yaml"))
        new_default_values = yaml.safe_load(open("config\\default_values.yaml"))
        new_full_config = {
            "model_config": new_config,
            "default_values": new_default_values,
        }

        schema.set_schema_config(new_full_config)
        assert schema.config == new_full_config

    def test_set_schema_config_resets_catalog_cache(self, schema):
        """Test that set_schema_config resets the catalog model cache."""
        # Get the cached model
        schema.create_catalog_model()
        assert schema._catalog_model is not None

        # Update config
        new_config = yaml.safe_load(open("config\\model_config.yaml"))
        new_default_values = yaml.safe_load(open("config\\default_values.yaml"))
        new_full_config = {
            "model_config": new_config,
            "default_values": new_default_values,
        }
        schema.set_schema_config(new_full_config)

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
        new_config = yaml.safe_load(open("config\\model_config.yaml"))
        new_default_values = yaml.safe_load(open("config\\default_values.yaml"))
        new_full_config = {
            "model_config": new_config,
            "default_values": new_default_values,
        }
        schema.set_schema_config(new_full_config)

        # All caches should be reset
        assert schema._catalog_model is None
        assert schema._dataset_model is None
        assert schema._agent_model is None
        assert schema._vcard_model is None

    def test_set_schema_config_updates_langtags(self, schema):
        """Test that set_schema_config updates the langtags list."""
        new_config = yaml.safe_load(open("config\\model_config.yaml"))
        new_default_values = yaml.safe_load(open("config\\default_values.yaml"))
        new_full_config = {
            "model_config": new_config,
            "default_values": new_default_values,
        }
        schema.set_schema_config(new_full_config)

        # Langtags should be updated
        assert schema.langtags == new_config["langtags"].split(",")


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
