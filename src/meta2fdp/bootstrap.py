import meta2fdp.models.HRIcore.v2 as HRIcore_v2
from meta2fdp.models.registry import ModelRegistry


def register_models():
    registry = ModelRegistry()
    registry.register("HRIcore", "2.0", HRIcore_v2)
    return registry
