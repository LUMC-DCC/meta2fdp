import csvparser
import pytest
from rdflib import URIRef, BNode, Graph, Literal
from rdflib.namespace import DCAT, DCTERMS

class DummyClient:
	def __init__(self):
		self.URL = URIRef("http://fdp.example/")
		self.PURL = "http://purl.example/"
		self.upload_calls = []
		self.publish_calls = []

	def upload_resource(self, graph, url, resource_type=None, resource_name=None):
		# record minimal info
		self.upload_calls.append({"graph": graph, "url": url, "resource_type": resource_type, "resource_name": resource_name})
		return "http://purl.example/catalog/1"

	def publish_metadata(self, purl):
		self.publish_calls.append(purl)


def make_csv(path, header, row):
	# simple helper to write a semicolon separated csv
	with open(path, "w", encoding="utf-8") as f:
		f.write(";".join(header) + "\n")
		f.write(";".join(row) + "\n")


def test_parse_cat_dat_uploads_and_publishes(tmp_path, monkeypatch):
	# prepare files
	cat_file = tmp_path / "catalogs.csv"
	dat_file = tmp_path / "datasets.csv"
	# include some columns to satisfy pd.read_csv and any minimal access
	header = ["title_en", "title_nl", "description_en", "description_nl", "contactPoint_email"]
	row = ["TitleEN", "TitleNL", "DescEN", "DescNL", "cp@example.org"]
	make_csv(cat_file, header, row)
	make_csv(dat_file, ["id"], ["dataset1"])

	client = DummyClient()

	# patch CSVParser methods and module helpers to no-op / controlled behavior
	monkeypatch.setattr(csvparser.CSVParser, "sempyro_catalog", lambda self, catalog, graph, url: BNode("catalog1"))
	monkeypatch.setattr(csvparser.CSVParser, "sempyro_dataset", lambda self, dataset, graph, purl: None)
	monkeypatch.setattr(csvparser, "subject_replace", lambda *args, **kwargs: None)
	monkeypatch.setattr(csvparser, "get_dataset_nodes", lambda g: [])  # avoid dataset loop that references undefined PURL variable

	parser = csvparser.CSVParser(config={}, client=client)
	# ensure parser has a graph object
	parser.graph = Graph()

	# run with publish=True
	parser.parse_cat_dat(str(cat_file), str(dat_file), publish=True)

	# assertions: one upload for the catalog, and publish called
	assert len(client.upload_calls) == 1
	assert client.upload_calls[0]["resource_type"] == DCAT.Catalog
	assert len(client.publish_calls) == 1
	assert client.publish_calls[0] == "http://purl.example/catalog/1"


def test_parse_cat_dat_does_not_publish_when_flag_false(tmp_path, monkeypatch):
	# prepare files
	cat_file = tmp_path / "catalogs.csv"
	dat_file = tmp_path / "datasets.csv"
	header = ["title_en", "title_nl", "description_en", "description_nl", "contactPoint_email"]
	row = ["TitleEN", "TitleNL", "DescEN", "DescNL", "cp@example.org"]
	make_csv(cat_file, header, row)
	make_csv(dat_file, ["id"], ["dataset1"])

	client = DummyClient()

	# same monkeypatches as previous test
	monkeypatch.setattr(csvparser.CSVParser, "sempyro_catalog", lambda self, catalog, graph, url: BNode("catalog1"))
	monkeypatch.setattr(csvparser.CSVParser, "sempyro_dataset", lambda self, dataset, graph, purl: None)
	monkeypatch.setattr(csvparser, "subject_replace", lambda *args, **kwargs: None)
	monkeypatch.setattr(csvparser, "get_dataset_nodes", lambda g: [])

	parser = csvparser.CSVParser(config={}, client=client)
	parser.graph = Graph()

	# run with publish=False
	parser.parse_cat_dat(str(cat_file), str(dat_file), publish=False)

	# assertions: one upload for the catalog, no publish calls
	assert len(client.upload_calls) == 1
	assert len(client.publish_calls) == 0