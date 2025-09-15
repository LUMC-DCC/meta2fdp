"""Excel parser for BEAT COVID and CoMoDuLate metadata. This class is a proof of concept of using a single excel file to describe metadata of a study represented as a catalog and its associated datasets on a FDP. It handles the seperation of individual classes into seperate sheets and the use of columns for creator attribution. 
"""
import pandas as pd
from rdflib import Graph, BNode, RDF, Literal, URIRef, FOAF, DCAT, DCTERMS, XSD
import keyring
from typing import Union

import yaml
from datetime import datetime

from os import getenv
from pathlib import Path
import sys
path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))

from fdp.FDPClient import FDPClient
from converter import Converter
from graphutils import merge_desc, subject_replace


class ExcelParser(Converter):

    def __init__(self, file_path, config, client = FDPClient, class_map=None, debug=False):
        super().__init__(class_map, debug)
        self.config = config
        self.client = client
        self.file_path = file_path

    def sheet_to_rdf(self, node_id, resource_type, sheet, graph: Graph, shacl):
        """
        For a given table or sheet, turn the values into RDF statements
        based on the content of a given shacl.  

        :param node_id: Id that should be used to track this resource node
        :type node_id: str
        :param resource_type: rdf class / node type that is being generated
        :type resource_type: str
        :param sheet: table/sheet that contains a URI and a Value column
        :type sheet: DataFrame
        :param graph: Graph where sheet should be stored as a rdf representation (node + properties)
        :type graph: Graph
        :param shacl: shacl file location
        :type shacl: str
        """
        pred_val = sheet.loc[:,["URI", "Value"]]
        resource = BNode(node_id) 
        self.node_log[resource_type] = resource #log the id of the resource node
        graph.add((resource, RDF.type, self.convert_prefix(self.class_map[resource_type]))) # add resource type to node
        last_predicate = "" # storage of last predicate, this is to handle multiple values where the description is not copied from previous row
        pred_val["URI"] = pred_val.apply(lambda row: self.convert_prefix(row["URI"]), axis=1) #convert prefixes to full URI's
        for index, row in pred_val.iterrows(): # add properties to node
            if row["URI"] == "previous" and type(row["Value"]) != float:
                graph.add(((resource, last_predicate, self.enforce_dtype(last_predicate, row["Value"], shacl))))
            elif row["URI"] == "previous" and type(row["Value"]) == float: # if both URI and value are empty, we skip the triple, as this is an empty row
                continue
            elif type(row["Value"]) == float:
                print("missing value for {}, {}".format(node_id, row["URI"]))
            else:
                graph.add(((resource, row["URI"], self.enforce_dtype(row["URI"], row["Value"], shacl) )))
                last_predicate = row["URI"]
        return node_id

    def parse_resources(self, data, sequence, shacl=None):
        """
        Loop through all required classes/sheets necessary to parse
        a resource into a compliant HRI resource description. 

        :param data: Pandas parsed excel file which is a dictionary of DataFrames with the sheet names as keys
        :type data: dict
        :param sequence: sequence of sheet names or resources to be parsed into RDF
        :type sequence: list
        :param shacl: filepath to shacl formatted data schema that the RDF should comply to
        :type shacl: str
        """
        for sheet_name in sequence:
            # loop through the sheets in the excel file
            #class_type = extractor.detect_class(data[sheet_name]) #experimental auto detections system
            #print(class_type)
            self.sheet_to_rdf(sheet_name, sheet_name, data[sheet_name], self.graph, shacl)

    def creator_column_to_rdf(self, column : dict, graph: Graph, dataset_id):
        """
        Creates a blank node in the given graph that
         represents a creator agent from a given dictionary.
        TODO make this work based on the URI's available in the sheet. 
        TODO value positions are now hardcoded

        :param column: value column in the given dataframe
        :type column: dict
        :param graph: The graph in which the node should be added
        :type graph: Graph
        :param dataset_id: Internal reference Id to be used for the node in the graph
        :type dataset_id: str
        """
        if column[1] == "unknown": #HACK agents should always have an ID, but for testing purpouses we can hash their names so we can show how the metadata will look like on a FDP
            creator = BNode(URIRef("example.org/id{}".format(str(hash(column[0])))))
            if self.debug:
                Warning("{column[0]} has no ID provided! using a hash of their name for now...".format())
        else:
            creator = BNode(URIRef(column[1]))
        graph.add((creator, RDF.type, FOAF.Agent)) # define node as an agent
        # add agent attributes
        graph.add((creator, FOAF.name, Literal(column[0])))
        if column[1] == "unknown":
            graph.add((creator, DCTERMS.identifier, Literal("example.org/id{}".format(str(hash(column[0]))))))
        else:
            graph.add((creator, DCTERMS.identifier, Literal(column[1])))
        graph.add((creator, FOAF.mbox, URIRef("mailto:" + column[3])))
        graph.add((creator, FOAF.homepage, URIRef(column[4])))
        # link dataset node id to creator
        graph.add((BNode(dataset_id), DCTERMS.creator, creator))


    def creator_sheet_to_rdf(self, sheet, graph: Graph, dataset_id):
        """
        Obtain a list of creator nodes id's that are added to a given graph
        RDF version of data lives in the graph and can be found through the list
        of blanknode internal id's that are returned in the list.
        This is done so when in the future there are datasets in a filled in form that
        have different sets of creators, we can attached the right creator to right dataset.  

        :param sheet: table / sheet containing creator metadata
        :type sheet: DataFrame
        :param graph: Graph in which the creator nodes should be added
        :type graph: Graph
        :param dataset_id: associated dataset (should already exist in the graph)
        :type dataset_id: str
        """ 
        sheet_dict = sheet.iloc[:,7:].to_dict() #HACK assumes the template stays the same order as original
        for key in sheet_dict.keys():
            self.creator_column_to_rdf(sheet_dict[key], graph, dataset_id)
            #TODO sort based on last names and add to class variable

    def parse_creator(self, data, sequence, creator_link):
        """
        This function parses the creator sheets associated with
        the datasets found in the creator_link dictionary.
        It removes values that are guides for the human data owner to 
        understand relationships between sheets.
        Then adds the relationships to the nodes describing the sheets
        using the interally assigned ID.

        :param data: pandas parsed excel sheet
        :type data: dict
        :param sequence: sheets to parse
        :type sequence: list
        :param creator_link: log of sheet relationships between dataset and creator sheets
        :type creator_link: dict
        """
        for sheet_name in sequence:
            # loop through the sheets in the excel file
            dataset_id = creator_link[sheet_name]
            self.graph.remove((BNode(dataset_id), DCAT.contactPoint, None))
            self.graph.remove((BNode(dataset_id), DCTERMS.creator, None))
            self.graph.remove((BNode(dataset_id), DCTERMS.publisher, None))
            self.graph.add((BNode(dataset_id), DCAT.contactPoint, BNode("Catalog_contactpoint")))
            self.graph.add((BNode(dataset_id), DCTERMS.publisher, BNode("Catalog_publisher")))
            self.creator_sheet_to_rdf(data[sheet_name], self.graph, dataset_id) 

    def _count_datasets(self, data):
        """
        This is a function that calculates the amount of datasets 
        that are present in the excel input.
        it assumes that every dataset sheet has a creator sheet 
        associated with a standard naming pattern

        :param data:  pandas parsed excel sheet
        :type data: dict
        :return: sequence of sheets to parse for dataset RDF node generation and recording of links between sheets
        :rtype: list, dict
        """
        # This might not be a good way to do things:
        dataset_counts = 0
        sheet_count = len(data.keys())
        if sheet_count >= 7:
            dataset_sheets = sheet_count - 5
            assert dataset_sheets % 2 == 0, "bad sheet count, are you following Dataset_x + Dataset_x_creator pattern?"
            dataset_counts = dataset_sheets // 2
            # dataset_counts += int(((sheet_count - 5) / 2))

        dataset_sequence = []
        creator_link = {}
        for x in range(1, dataset_counts + 1):
            # add the extra datasets and creators to the sequence
            dataset_name = 'Catalog_dataset_{}'.format(x)
            dataset_sequence.append(dataset_name)
            self.dataset_ids.append(dataset_name)
            self.class_map[dataset_name] = 'dcat:Dataset'
            # link creator sheet to dataset sheet.
            creator_link['Dataset_{}_creator'.format(x)] = dataset_name
            self.class_map['Dataset_{}_creator'.format(x)] = 'foaf:Agent'
        return dataset_sequence, creator_link

    def read_excel(self, file_path=None):
        """
        This function reads a given excel file or the
        default excel assigned when constructing the Class

        :param filepath: file path to excel sheet
        :type filepath: str
        :return: parsed excel sheet
        :rtype: dict
        """
        if file_path:
            data = pd.read_excel(file_path, sheet_name=None)
        else:
            data = pd.read_excel(self.file_path, sheet_name=None)
        return data
    
    def update_email(self):
        """
        This function updates the emails of the contactpoint and publisher
        to conform with the health-ri schema pattern (add mailto:)
        """
        # find hasEmail statement for contactpoint from graph 
        result = self.graph.triples((BNode("Catalog_contactpoint"), URIRef(self.VCARD + "hasEmail"), None))
        for node, hasemail, email in result:
            self.graph.set((BNode("Catalog_contactpoint"), URIRef(self.VCARD + "hasEmail"), URIRef("mailto:" + email))) #update triple
        result = self.graph.triples((BNode("Catalog_publisher"), FOAF.mbox, None))
        for node, hasemail, email in result:
            self.graph.set((BNode("Catalog_publisher"), FOAF.mbox, URIRef("mailto:" + email)))
    
    
    def parse_catalog(self, file_path=None, shacl="schema/shacl/v2/Catalog.ttl"):
        """
        Parse an excel file and extract catalog information from it.
        It uses the given Resource SHACL description to help assign
        value types.

        :param file_path: file path to excel
        :type file_path: str
        :param shacl: file path to shacl
        :type shacl: str
        """
        data = self.read_excel(file_path)
        # possible lists of sheet names to parse for specific resources
        # project_sequence = ['Project'] 
        catalog_sequence = ['Catalog', 'Catalog_contactpoint', 'Catalog_publisher']
        # catalog_service = ['Catalog_service']
        # catalog to RDF
        self.parse_resources(data, catalog_sequence, shacl)
        # remove all user hints from the data:
        self.graph.remove((BNode('Catalog'), DCAT.contactPoint, None))
        self.graph.remove((BNode('Catalog'), DCTERMS.publisher, None))
        self.graph.remove((BNode('Catalog'), DCAT.dataset, None))
        self.graph.remove((BNode('Catalog'), DCAT.service, None))
        # add our agents to the catalog:
        self.graph.add((BNode('Catalog'), DCAT.contactPoint, BNode('Catalog_contactpoint')))
        # update the contactpoint email pattern to "mailto:"
        self.update_email()
        self.graph.add((BNode('Catalog'), DCTERMS.publisher, BNode('Catalog_publisher')))
        #print(self.graph.serialize())
        del(data)
    
    def parse_dataset(self, file_path=None, shacl=None):
        """
        Parse excel file and extract dataset information from it.

        :param file_path: path to file
        :type file_path: str
        :param schacl: path to shacl
        :type shacl: str
        """
        data = self.read_excel(file_path)
        # dataset to RDF
        dataset_sequence, creator_link = self._count_datasets(data)
        self.parse_resources(data, dataset_sequence, shacl)
        self.parse_creator(data, creator_link.keys(), creator_link)

        #print(self.graph.serialize())
    

    def dataset_upload(self, dataset_graph: Graph, catalog_purl: str, fdp_dataset_dictionary: dict=None) -> Union[Graph, str]:
        """Upload a dataset based on the different modes available in the config

        :param dataset_graph: metadata of a dataset.
        :type dataset_graph: Graph
        :param catalog_purl: URL of the catalog the dataset is part of
        :type catalog_purl: str
        :param fdp_dataset_dictionary: _description_, defaults to None
        :type fdp_dataset_dictionary: dict, optional
        :return: Graph
        """
        if self.config["mode"]["replace"] == True:
            try:
                dataset_identifier = dataset_graph.value(subject=URIRef(PURL + "new"), predicate=DCTERMS.identifier)
                matching_purl = fdp_dataset_dictionary[dataset_identifier]
                self.client.update_resource(matching_purl, DCAT.Dataset, dataset_graph)
            except KeyError:
                Warning("Missing dataset on FDP: {dataset_identifier} ")
                resource_string = self.client.link_resource(dataset_graph, catalog_purl, DCAT.Dataset)
                dataset_purl = self.client.upload_data(dataset_graph.serialize(), "Dataset")
                if self.config["mode"]["publish"]:
                    self.client.publish_metadata(dataset_purl)
                return resource_string
        else:
            resource_string = self.client.link_resource(dataset_graph, catalog_purl, DCAT.Dataset)
            dataset_purl = self.client.upload_data(dataset_graph.serialize(), "Dataset")
            if self.config["mode"]["publish"]:
                    self.client.publish_metadata(dataset_purl)


    def parse(self):
        self.parse_catalog(shacl=self.config["file_paths"]["catalog_shacl"])
        subject_replace(PURL + "new", BNode("Catalog"), DCAT.Catalog, self.graph)
        if self.config["mode"]["replace"] == True:
            catalog_purl = self.config["FDP"]["catalog_purl"]
            updated_catalog = self.client.update_catalog(catalog_purl, self.graph)
        else:
            catalog_purl = client.upload_resource(self.graph, URL, resource_type=DCAT.Catalog)
            updated_catalog = None
        print("datasets")
        self.parse_dataset(self.config["file_paths"]["datasets_input_file"], shacl=self.config["file_paths"]["dataset_shacl"])
        catalog_description = next(self.graph.triples((None, DCTERMS.description, None)))
        
        for dataset_node_id in self.dataset_ids:
            dataset = self.graph.cbd(BNode(dataset_node_id))
            dataset.remove((BNode(dataset_node_id), DCTERMS.isReferencedBy, Literal("Links to BEAT publications:")))
            dataset.remove((BNode(dataset_node_id), DCTERMS.isReferencedBy, Literal("Links to BEAT publications")))
            if self.config["file_paths"]["catalog_input_file"] == "data/BEAT/Health-RI Core Metadata model v2 filled BEAT.xlsx":
                dataset.add((BNode(dataset_node_id), DCTERMS.issued, Literal(datetime(year=2024,month=2, day=4).isoformat(), datatype=XSD.dateTime)))
                dataset.add((BNode(dataset_node_id), DCTERMS.modified, Literal(datetime(year=2024,month=2, day=4).isoformat(), datatype=XSD.dateTime)))
            elif self.config["file_paths"]["catalog_input_file"] == "data/BEAT/Health-RI Core Metadata model v2 filled Comodulate.xlsx":
                dataset.add((BNode(dataset_node_id), DCTERMS.issued, Literal(datetime(year=2025,month=4, day=4).isoformat(), datatype=XSD.dateTime)))
                dataset.add((BNode(dataset_node_id), DCTERMS.modified, Literal(datetime(year=2025,month=4, day=4).isoformat(), datatype=XSD.dateTime)))
            dataset.add((BNode(dataset_node_id), DCTERMS.license, URIRef(config["default_values_metadata"]["license"])))
            dataset.add((BNode(dataset_node_id), URIRef("http://data.europa.eu/r5r/applicableLegislation")  , URIRef("http://data.europa.eu/eli/reg/2025/327/oj")))
            # add catalog description:
            dataset.add((BNode(dataset_node_id), DCTERMS.description, catalog_description[2]))
            merge_desc(BNode(dataset_node_id), dataset)
            subject_replace(PURL + "new", BNode(dataset_node_id), DCAT.Dataset, dataset) # replace mode also assumes FDP resource PURL
            self.dataset_upload(dataset, catalog_purl, datasets_fdp_ids)  #FIXME This function needs the id's of dataset children of the catalog

if __name__ == "__main__":
    conf_path = getenv("CONF_PATH", default="config/configuration.yaml")

    # get default values from config file
    with open(conf_path, "r") as config_file:
        config = yaml.safe_load(config_file)

    def connect_client():
        ### set up connection settings to FDP server ###
        URL = URIRef(config["FDP"]["URL"])
        PURL = URIRef(config["FDP"]["PURL"])
        client = FDPClient(URL, config["keyring"]["username"], keyring.get_password(config["keyring"]["fdp_service"], config["keyring"]["username"]), PURL)
        # ping server:
        client.check_url(URL)
        return URL, PURL, client

    URL, PURL, client = connect_client()
    file_path = config["file_paths"]["catalog_input_file"]
    parser = ExcelParser(file_path=file_path, config=config, client=client)
    parser.parse()
    