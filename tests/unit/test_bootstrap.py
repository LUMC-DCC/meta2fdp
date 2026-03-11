"""Test cases for the bootstrap module of meta2fdp."""

import meta2fdp.bootstrap as bootstrap


def test_register_models():
    registry = bootstrap.register_models()
    assert registry is not None
    assert "HRIcore" in registry.list_schemas()
    assert "v2" in registry.list_versions("HRIcore")
    assert registry.get("HRIcore", "v2") is not None
