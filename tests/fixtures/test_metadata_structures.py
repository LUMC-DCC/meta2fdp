import pytest
import pandas as pd


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
def test_catalog_metadata_df(test_catalog_metadata):
    return pd.DataFrame(data=test_catalog_metadata)


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


@pytest.fixture
def test_dataset_metadata_df(test_dataset_metadata):
    return pd.DataFrame(data=test_dataset_metadata)
