import yaml
import pytest
import pandas as pd
from pathlib import Path
from rdflib import URIRef, Graph
from sempyro import LiteralField, hri_dcat
from meta2fdp.schemas.hriv2schema import Hriv2Schema as Schema


@pytest.fixture(scope="module")
def data_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data"


@pytest.fixture(scope="module")
def config(data_dir: Path):
    conf_path = data_dir / "config" / "model_config_test.yaml"
    with open(conf_path, "r") as config_file:
        return yaml.safe_load(config_file)


@pytest.fixture
def schema(config):
    return Schema(config)


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
        index=["support_email", "support_name"],
    )
    result = schema.instantiate_HRIVcard(test_metadata, prefix="support")
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
            "applicableLegislation",
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
