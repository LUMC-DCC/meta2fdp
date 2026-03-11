"""Test cases for the base configuration of meta2fdp."""

import pytest
from meta2fdp.config.schema import SchemaConfig
from meta2fdp.bootstrap import register_models


@pytest.fixture
def registry():
    return register_models()


def test_schema_config(registry):

    config = SchemaConfig(
        name="HRIcore_v2",
        type="schema",
        schema_name="HRIcore",
        schema_version="v2",
    )

    assert config.validate_config(registry) is True
    public_dict = config.public_dict()
    assert public_dict["name"] == "HRIcore_v2"
    assert public_dict["type"] == "schema"
    assert public_dict["schema"] == "HRIcore"
    assert public_dict["version"] == "v2"
