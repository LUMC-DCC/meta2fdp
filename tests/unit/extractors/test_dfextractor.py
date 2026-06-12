import pytest
from meta2fdp.extractors.dfextractor import DFExtractor
from meta2fdp.config.extractor.extractor import ExtractorConfig
import pandas as pd


@pytest.fixture
def config():
    return ExtractorConfig(
        name="test_extractor",
        extractor_type="df",
        mappings={
            "title": "title",
            "description": "description",
            "identifier": "identifier",
        },
    )


@pytest.fixture
def langtag_config():
    return ExtractorConfig(
        name="test_extractor",
        extractor_type="df",
        mappings={
            "title": "title",
            "description": "description",
            "identifier": "identifier",
            "lang_tags": "en,nl",
        },
    )


def test_map_metadata(config):
    """Tests the map_metadata function of the DFExtractor class. This test checks if the function correctly maps columns from the input dataframe to the expected output column names based on the provided properties mapping. It also verifies that optional properties are handled correctly by adding columns filled with pd.NA when they are not present in the input dataframe. The test asserts that the resulting dataframe has the expected columns and that optional properties are filled with pd.NA as expected."""
    extractor = DFExtractor(config)
    df = pd.DataFrame(
        {
            "title": ["Dataset 1", "Dataset 2"],
            "description": ["Description 1", "Description 2"],
            "identifier": ["id1", "id2"],
            "extra_column": ["extra1", "extra2"],
        }
    )
    properties = {
        "title": "title",
        "description": "description",
        "identifier": "identifier",
        "optional_property": None,
    }
    result_df = extractor.map_metadata(df, properties)
    assert set(result_df.columns) == {
        "title",
        "description",
        "identifier",
        "optional_property",
    }
    assert result_df["optional_property"].isna().all()


def test_map_metadata_lang_tags(langtag_config):

    extractor = DFExtractor(langtag_config)
    df = pd.DataFrame(
        {
            "title_en": ["Dataset 1", "Dataset 2"],
            "title_nl": ["dataset 1", "dataset 2"],
            "description_en": ["Description 1", "Description 2"],
            "description_nl": ["omschrijving 1", "omschrijving 2"],
            "identifier": ["id1", "id2"],
        }
    )
    properties = {
        "title": "title",
        "description": "description",
        "identifier": "identifier",
    }
    result_df = extractor.map_metadata(df, properties)
    assert set(result_df.columns) == {
        "title_en",
        "title_nl",
        "description_en",
        "description_nl",
        "identifier",
    }
    assert result_df["title_en"].tolist() == ["Dataset 1", "Dataset 2"]
    assert result_df["description_en"].tolist() == ["Description 1", "Description 2"]
    assert result_df["title_nl"].tolist() == ["dataset 1", "dataset 2"]
    assert result_df["description_nl"].tolist() == ["omschrijving 1", "omschrijving 2"]


def test_map_metadata_single_lang_tag(langtag_config):
    """Tests if two langtags are given in the config (done in the tests/config/mappings_test.yaml file) but only one is present in the dataframe, the function correctly uses the available langtag as a fallback for the missing one, and does not raise an error about missing required columns. This is to ensure that the function can handle cases where some language-specific columns are missing from the input dataframe, as long as at least one of the expected language-specific columns is present for each property."""
    extractor = DFExtractor(langtag_config)
    df = pd.DataFrame(
        {
            "title_en": ["Dataset 1", "Dataset 2"],
            "description_en": ["Description 1", "Description 2"],
            "identifier": ["id1", "id2"],
        }
    )
    properties = {
        "title": "title",
        "description": "description",
        "identifier": "identifier",
    }
    result_df = extractor.map_metadata(df, properties)
    assert set(result_df.columns) == {"title_en", "description_en", "identifier"}
    assert result_df["title_en"].tolist() == ["Dataset 1", "Dataset 2"]
    assert result_df["description_en"].tolist() == ["Description 1", "Description 2"]


def test_map_metadata_missing_required_column(config):
    extractor = DFExtractor(config)
    df = pd.DataFrame(
        {
            "title": ["Dataset 1", "Dataset 2"],
            "description": ["Description 1", "Description 2"],
            # "identifier" column is missing
        }
    )
    properties = {
        "title": "title",
        "description": "description",
        "identifier": "identifier",
    }
    with pytest.raises(KeyError) as exc_info:
        extractor.map_metadata(df, properties)
    assert "Missing expected columns in dataframe: ['identifier']" in str(
        exc_info.value
    )


def test_parse_catalog(config):
    """Tests the parse_catalog function of the DFExtractor class. This test checks if the function correctly maps and flattens nested catalog-related fields (such as publisher, contactPoint, and creator) from the input dataframe to the expected output column names based on the provided mappings. It asserts that the resulting dataframe has the expected columns and values, and that missing values are handled as pd.NA."""
    extractor = DFExtractor(config)
    df = pd.DataFrame(
        {
            "title": ["catalog 1", "catalog 2"],
            "description": ["Description 1", "Description 2"],
            "identifier": ["id1", "id2"],
            "publisher_name": ["Publisher", None],
            "publisher_email": ["publisher@example.com", None],
            "publisher_identifier": ["publisher_id", None],
            "contactPoint_email": ["contact@example.com", None],
            "contactPoint_name": ["Contact Person", None],
            "creator_name": ["Creator Person", None],
            "creator_email": ["creator@example.com", None],
            "creator_identifier": ["creator_id", None],
        }
    )
    extractor.config.mappings = {
        "catalog": {
            "title": "title",
            "description": "description",
            "identifier": "identifier",
            "publisher": {
                "name": "publisher_name",
                "mbox": "publisher_email",
                "identifier": "publisher_identifier",
            },
            "contactPoint": {
                "hasEmail": "contactPoint_email",
                "formatted_name": "contactPoint_name",
            },
            "creator": {
                "name": "creator_name",
                "mbox": "creator_email",
                "identifier": "creator_identifier",
            },
        },
    }
    result_list = extractor.parse_catalog(df)
    assert result_list == [
        {
            "title": "catalog 1",
            "description": "Description 1",
            "identifier": "id1",
            "publisher_name": "Publisher",
            "publisher_mbox": "publisher@example.com",
            "publisher_identifier": "publisher_id",
            "contactPoint_hasEmail": "contact@example.com",
            "contactPoint_formatted_name": "Contact Person",
            "creator_name": "Creator Person",
            "creator_mbox": "creator@example.com",
            "creator_identifier": "creator_id",
        },
        {
            "title": "catalog 2",
            "description": "Description 2",
            "identifier": "id2",
            "publisher_name": None,
            "publisher_mbox": None,
            "publisher_identifier": None,
            "contactPoint_hasEmail": None,
            "contactPoint_formatted_name": None,
            "creator_name": None,
            "creator_mbox": None,
            "creator_identifier": None,
        },
    ]


def test_parse_dataset(config):
    """Tests the parse_dataset function of the DFExtractor class. This test checks if the function correctly maps and flattens nested dataset-related fields from the input dataframe to the expected output column names based on the provided mappings. It asserts that the resulting dataframe has the expected columns and values, and that missing values are handled as pd.NA."""
    extractor = DFExtractor(config)
    df = pd.DataFrame(
        {
            "title": ["dataset 1", "dataset 2"],
            "description": ["Description 1", "Description 2"],
            "identifier": ["id1", "id2"],
            "publisher_name": ["Publisher", None],
            "publisher_email": ["publisher@example.com", None],
            "publisher_identifier": ["publisher_id", None],
            "contactPoint_email": ["contact@example.com", None],
            "contactPoint_name": ["Contact Person", None],
            "creator_name": ["Creator Person", None],
            "creator_email": ["creator@example.com", None],
            "creator_identifier": ["creator_id", None],
        }
    )
    extractor.config.mappings = {
        "dataset": {
            "title": "title",
            "description": "description",
            "identifier": "identifier",
            "publisher": {
                "name": "publisher_name",
                "mbox": "publisher_email",
                "identifier": "publisher_identifier",
            },
            "contactPoint": {
                "hasEmail": "contactPoint_email",
                "formatted_name": "contactPoint_name",
            },
            "creator": {
                "name": "creator_name",
                "mbox": "creator_email",
                "identifier": "creator_identifier",
            },
        },
    }
    result_list = extractor.parse_dataset(df)
    assert result_list == [
        {
            "title": "dataset 1",
            "description": "Description 1",
            "identifier": "id1",
            "publisher_name": "Publisher",
            "publisher_mbox": "publisher@example.com",
            "publisher_identifier": "publisher_id",
            "contactPoint_hasEmail": "contact@example.com",
            "contactPoint_formatted_name": "Contact Person",
            "creator_name": "Creator Person",
            "creator_mbox": "creator@example.com",
            "creator_identifier": "creator_id",
        },
        {
            "title": "dataset 2",
            "description": "Description 2",
            "identifier": "id2",
            "publisher_name": None,
            "publisher_mbox": None,
            "publisher_identifier": None,
            "contactPoint_hasEmail": None,
            "contactPoint_formatted_name": None,
            "creator_name": None,
            "creator_mbox": None,
            "creator_identifier": None,
        },
    ]
