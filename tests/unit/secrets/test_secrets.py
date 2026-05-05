import pytest

from meta2fdp.secrets.base import SecretsProvider
from meta2fdp.secrets.compositeprovider import CompositeSecretsProvider
from meta2fdp.secrets.environmentprovider import EnvSecretsProvider
from meta2fdp.secrets.keyringprovider import KeyringSecretsProvider


def test_secrets_provider_is_abstract():
    with pytest.raises(TypeError):
        SecretsProvider()


def test_env_secrets_provider_returns_env_value(monkeypatch):
    monkeypatch.setenv("TEST_SECRET_VALUE", "supersecret")
    provider = EnvSecretsProvider()

    assert provider.get("TEST_SECRET_VALUE") == "supersecret"


def test_env_secrets_provider_returns_none_when_missing(monkeypatch):
    monkeypatch.delenv("TEST_SECRET_MISSING", raising=False)
    provider = EnvSecretsProvider()

    assert provider.get("TEST_SECRET_MISSING") is None


def test_keyring_secrets_provider_delegates_to_keyring(monkeypatch):
    recorded = {}

    def fake_get_password(service_name, key_name):
        recorded["args"] = (service_name, key_name)
        return "keyring-secret"

    monkeypatch.setattr(
        "meta2fdp.secrets.keyringprovider.keyring.get_password",
        fake_get_password,
    )

    provider = KeyringSecretsProvider(service_name="service-name")
    result = provider.get("api_token")

    assert result == "keyring-secret"
    assert recorded["args"] == ("service-name", "api_token")


class _DummyProvider:
    def __init__(self, return_value):
        self.return_value = return_value

    def get(self, name):
        return self.return_value


def test_composite_secrets_provider_returns_first_available_value():
    provider = CompositeSecretsProvider(
        [
            _DummyProvider(None),
            _DummyProvider("first-available"),
            _DummyProvider("unused"),
        ]
    )

    assert provider.get("any-name") == "first-available"


def test_composite_secrets_provider_raises_key_error_when_missing():
    provider = CompositeSecretsProvider(
        [
            _DummyProvider(None),
            _DummyProvider(None),
        ]
    )

    with pytest.raises(KeyError, match="Secret 'missing' not found"):
        provider.get("missing")
