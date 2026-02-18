import unittest
import yaml
import pathlib
import sys


BASE_DIR = pathlib.Path(__file__).resolve().parent

# facilitate running tests from command line using `python -m unittest`
sys.path.append(str(BASE_DIR.parent / 'src'))

from meta2fdp.converters.hriv2model import Hriv2Model as Model
import pandas as pd
from sempyro import LiteralField, hri_dcat
from rdflib import URIRef, Graph
import yaml


model_config_path = pathlib.Path("tests/test_files/test_configs/model_config_test.yaml")

def parse_yaml(conf_path):
        try:
            with open(conf_path, "r") as config_file:
                config = yaml.safe_load(config_file)  # used to obtain right value types from the yaml like booleans
                return config
        except FileNotFoundError:
            print(f"YAML file not found: {conf_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")
            sys.exit(1) 

model_config = parse_yaml(model_config_path)

class test_Hriv2Model(unittest.TestCase):
     
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.config = model_config
        self.model = Model(self.config)
        
    
    def test_lang_literals_(self):
        test_metadata = pd.Series(data=["English_tag", "Nederlandse_label",], index=["tag_en", "tag_nl"])
        expected_result = [LiteralField(value="English_tag", language="en"), LiteralField(value="Nederlandse_label", language="nl")]
        self.assertEqual(expected_result, self.model.lang_literals(test_metadata, "tag"))

        test_metadata_override = pd.Series(data=["English_tag", "Nederlandse_label", "no_label"], index=["tag_en", "tag_nl", "tag"])
        expected_result_override = [LiteralField(value="no_label")]
        self.assertEqual(expected_result_override, self.model.lang_literals(test_metadata_override, "tag"))

        test_metadata_nolang = pd.Series(data=["no_label"], index=["tag"])
        expected_result_nolabel = [LiteralField(value="no_label")]
        self.assertEqual(expected_result_nolabel, self.model.lang_literals(test_metadata_nolang, "tag"))

    
    @unittest.expectedFailure
    def test_fail_lang_literals(self):
         self.model.lang_literals(pd.Series(), "tag")


    def test_convert_class_to_rdf(self):
        vcard = hri_dcat.HRIVCard(hasEmail="mailto:" +"anemail@test.io", formatted_name=LiteralField(value="anem ail"))
        expected_graph = Graph().parse(data="""@prefix v: <http://www.w3.org/2006/vcard/ns#> .

<http://fdp.org/new> a v:Kind ;
    v:fn "anem ail" ;
    v:hasEmail <mailto:anemail@test.io> .""", format="ttl")
         
        result_graph = self.model.convert_class_to_rdf(vcard, URIRef("http://fdp.org/new"))
        unique_triples = expected_graph ^ result_graph
        self.assertIs(len(unique_triples), 0, msg=f"Serialized graphs are not the same! These are the unexpected triples{unique_triples.serialize()}")

    def test_instantiate_HRIVcard(self):
        test_metadata = pd.Series(
            data=["contact@example.com", "John Doe"],
            index=["contactPoint_email", "contactPoint_name"]
        )
        result = self.model.instantiate_HRIVcard(test_metadata)
        self.assertEqual(str(result.hasEmail), "mailto:contact@example.com")
        self.assertEqual(result.formatted_name.value, "John Doe")

    def test_instantiate_HRIVcard_custom_prefix(self):
        test_metadata = pd.Series(
            data=["support@example.com", "Support Team"],
            index=["support_email", "support_name"]
        )
        result = self.model.instantiate_HRIVcard(test_metadata, prefix="support")
        self.assertEqual(str(result.hasEmail), "mailto:support@example.com")
        self.assertEqual(result.formatted_name.value, "Support Team")

    def test_instantiate_agent(self):
        test_metadata = pd.Series(
            data=["Dr. Jane Smith", "agent-123", "https://example.org", "jane@example.com"],
            index=["creator_name", "creator_identifier", "creator_url", "creator_email"]
        )
        result = self.model.instantiate_agent(test_metadata, "creator")
        self.assertEqual(result.name[0].value, "Dr. Jane Smith")
        self.assertEqual(result.identifier, ["agent-123"])
        self.assertEqual(str(result.homepage),"https://example.org/")
        self.assertEqual(str(result.mbox), "mailto:jane@example.com")

    def test_instantiate_HRICatalog(self):
        catalog_metadata = pd.Series(
            data=["Sample Catalog", "A test catalog"],
            index=["title", "description"]
        )
        vcard = hri_dcat.HRIVCard(hasEmail="mailto:contact@test.io", formatted_name=LiteralField(value="Contact"))
        agent = hri_dcat.HRIAgent(name=[LiteralField(value="Publisher")], identifier=["pub-1"], mbox="mailto:pub@test.io", homepage="http://example.org")
        
        result = self.model.instantiate_HRICatalog(catalog_metadata, vcard, agent)
        self.assertEqual(result.title[0].value, "Sample Catalog")
        self.assertEqual(result.description[0].value, "A test catalog")
        self.assertEqual(result.contact_point, vcard)
        self.assertEqual(result.publisher, agent)
        self.assertEqual(result.dataset, [])

    def test_instantiate_HRIDataset(self):
        dataset_metadata = pd.Series(
            data=["Test Dataset", "A dataset for testing", "dataset-001", "HEAL", "PUBLIC", "keyword1,keyword2", "http://example.org/legislation", "1000", "500"],
            index=["title", "description", "identifier", "theme", "accessRights", "keywords", "applicableLegislation", "numberOfRecords", "numberOfUniqueIndividuals"]
        )
        vcard = hri_dcat.HRIVCard(hasEmail="mailto:contact@test.io", formatted_name=LiteralField(value="Contact"))
        agent = hri_dcat.HRIAgent(name=[LiteralField(value="Publisher")], identifier=["pub-1"], mbox="mailto:pub@test.io", homepage="http://example.org")
        creators = [hri_dcat.HRIAgent(name=[LiteralField(value="Creator1")], identifier=["creator-1"], mbox="mailto:creator@test.io", homepage="http://example.org")]
        
        result = self.model.instantiate_HRIDataset(dataset_metadata, vcard, agent, creators)
        self.assertEqual(result.title[0].value, "Test Dataset")
        self.assertEqual(result.description[0].value, "A dataset for testing")
        self.assertEqual(result.identifier, "dataset-001")
        self.assertEqual(result.contact_point, vcard)
        self.assertEqual(result.creator, creators)
        self.assertEqual(result.publisher, agent)
        self.assertEqual(result.keyword, [LiteralField(value="keyword1"), LiteralField(value="keyword2")])
        self.assertEqual(result.number_of_records.value, "1000")
        self.assertEqual(result.number_of_unique_individuals.value, "500")


if __name__ == '__main__':
    unittest.main()


