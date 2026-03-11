import pytest
from meta2fdp.pipeline.publish_metadata import PublishMetadataPipeline
from meta2fdp.bootstrap import register_models
from meta2fdp.config.schema import SchemaConfig


@pytest.fixture
def registry():
    return register_models()


def test_publish_metadata_pipeline(registry):
    schema_config = SchemaConfig(
        name="HRIcore_v2",
        type="schema",
        schema_name="HRIcore",
        schema_version="v2",
    )

    pipeline = PublishMetadataPipeline(
        schema_config=schema_config, registries={"models": registry}
    )
    assert pipeline.schema_module is not None
    assert pipeline.schema_module == registry.get("HRIcore", "v2")
    pipeline.run()
