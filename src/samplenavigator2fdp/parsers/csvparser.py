"""
Adapter class from csv to FDP
"""
from samplenavigator2fdp.parsers.abstractparser import Parser
import pandas as pd
from abc import override
from pathlib import Path
import yaml

test = """@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix cat: <http://www.w3.org/ns/dcat#> .
@prefix dcat: <http://www.w3.org/ns/dcat#> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix og: <http://ogp.me/ns#> .
@prefix vcard: <http://www.w3.org/2006/vcard/ns#> .
@prefix dct: <http://purl.org/dc/terms/> .

<https://fdp.example.org/agent/publisher> dct:identifier "https://ror.org/05xvt9f17" ;
	rdf:type foaf:Agent ;
	foaf:homepage <https://www.lumc.nl> ;
	foaf:mbox <mailto:biobankorganisatie@lumc.nl> ;
	foaf:name "Leiden University Medical Center"@en, "Leids Universitair Medisch Centrum"@nl .

<https://fdp.example.org/contact/main> rdf:type vcard:Kind ;
	vcard:fn "Biobankorganisatie LUMC" ;
	vcard:hasEmail <mailto:biobankorganisatie@lumc.nl> .

<https://fdp.example.org/new> dct:description "A general description of the LUMC biobanks in English"@en, "Een algemene omschrijving van de LUMC biobanken in het Nederlands"@nl ;
	dct:publisher <https://fdp.example.org/agent/publisher> ;
	dct:title "LUMC Biobanks"@en, "LUMC Biobanken"@nl ;
	rdf:type dcat:Catalog ;
	dcat:contactPoint <https://fdp.example.org/contact/main> ;
	dcat:dataset <https://fdp.example.org/dataset/dataset> .
"""


class CSVParser(Parser):

    def __init__(self, config: Path):
        self.config = yaml.reader(config)

    @override
    def get_metadata(self, path: str) -> pd.DataFrame:
        return pd.read_csv(path, sep=";",header=0)

    @override
    def parse_catalog(self) -> pd.DataFrame:
        catalog_path = self.config["file_paths"]["catalog_input_file"]
        if catalog_path == "catalog_input_file":
            raise FileNotFoundError("catalog file path has not been set in config!")
        return self.get_metadata(catalog_path)
    
    @override
    def parse_dataset(self) -> pd.DataFrame:
        dataset_path = self.config["file_paths"]["dataset_input_file"]
        return self.get_metadata(dataset_path)


    @override
    def parse_distribution(self) -> pd.DataFrame:
        distribution_path = self.config["file_paths"]["distribution_input_file"]
        return self.get_metadata(distribution_path)

