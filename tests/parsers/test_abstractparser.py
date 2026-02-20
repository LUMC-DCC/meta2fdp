import pandas as pd
import pytest

from meta2fdp.parsers.abstractparser import AbstractParser


class DummyParser(AbstractParser):
    def get_metadata(self, path: str) -> pd.DataFrame:
        return pd.DataFrame()

    def parse_catalog(self) -> pd.DataFrame:
        return pd.DataFrame()

    def parse_dataset(self) -> pd.DataFrame:
        return pd.DataFrame()

    def parse_distribution(self) -> pd.DataFrame:
        return pd.DataFrame()

    def parse_dataservice(self) -> pd.DataFrame:
        return pd.DataFrame()

    def parse_datasetseries(self) -> pd.DataFrame:
        return pd.DataFrame()


def test_resolve_path_existing(tmp_path):
    f = tmp_path / "example.txt"
    f.write_text("ok")
    p = DummyParser(config={})
    resolved = p._resolve_path(str(f))
    assert resolved.exists()
    assert resolved == f.resolve()


def test_resolve_path_missing(tmp_path):
    f = tmp_path / "missing.txt"
    p = DummyParser(config={})
    with pytest.raises(FileNotFoundError):
        p._resolve_path(f)


def test_abstract_methods_return_dataframe():
    p = DummyParser(config={})
    assert isinstance(p.get_metadata(""), pd.DataFrame)
    assert isinstance(p.parse_catalog(), pd.DataFrame)
