import pandas as pd
from rdflib import Graph, BNode, RDF, Literal, URIRef, FOAF, DCAT, DCTERMS, XSD
from rdflib.namespace import Namespace


class HealthRIConverterv2:
    
    VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")

    def __init__(self, file_path,  class_map=None, debug=False):
        self.graph, self.prefix_map = self._prep_graph()
        self.file_path = file_path
        self.node_log = {}
        if class_map:
            self.class_map = class_map
        else:
            self.class_map = {'Project': "foaf:Project", 'Catalog': 'dcat:Catalog', 'Catalog_contactpoint': "vcard:Kind", 'Catalog_publisher': "foaf:Agent", 'Catalog_service': "dcat:DataService"}
        self.dataset_ids = []
        self.debug = debug

    def _gen_prefix_map(self, namespaces):
        prefix_map = {}
        for prefix, uri in namespaces:
            prefix_map[prefix.lower()] = uri
        prefix_map["dct"] = DCTERMS # map dct to the DCTERMS namespace, as the RDFLIB uses dcterms as a prefix instead.
        return prefix_map

    def _prep_graph(self):
        """
        Utility function to prepare data graph with the context
        of the Health-RI v2 metadata model.
        It also provides a reverse mapping of prefixes used within
        the context of the metadat model.

        :return: graph and prefix mapping
        :rtype: Graph, dict
        """
        # add VCARD to namespace as the default rdflib namesapce doesn't have it yet:
        graph = Graph(bind_namespaces="rdflib")
        graph.bind("vcard", self.VCARD)
        # reverse namespace prefix mapping so we can parse prefixes used in template
        prefix_map = self._gen_prefix_map(graph.namespaces())
        return graph, prefix_map

    def convert_prefix(self, string: str):
        """
        This function converts a string that contains a prefix into
        a full length uri that is able to be parsed by the RDFLib namespace.  
        :param string: string containing a prefix

        :type string: String
        :return: URI Reference
        :rtype: URIRef
        """
        if type(string) == float:
            return "previous"
        prefix, value = string.split(":")
        uri = self.prefix_map[prefix]
        return URIRef(uri + value)
        
    def enforce_dtype(self, URI, value, shacl_file):
        """
        Parses a shacl graph and extracts the RDF value type
        based on the URI associated with the value within the
        SHACL description.  
        Only works for Literals or URIRefs and assumes anything
        without a explicit nodeKind statement should be a literal.
        TODO Does not enforce sh:datatype yet!

        :param URI: URI that should also be in the SHACL
        :type URI: String
        :param value: value to be enforced
        :type value: String, int or float
        :return: RDF value type enforced value
        :rtype: Literal or URIRef
        """
        shacl = Graph()
        shacl.parse(shacl_file)
        res = shacl.triples( (None, self.convert_prefix("sh:path"), URI)) # find class statements where class has URI as property
        res2 = "NA"
        #print(self.convert_prefix("sh:IRI"))
        #TODO make sure that multiple hits are handled, for now takes the last result:
        for s,p,o in res: # from the class with URI as a property extract the explicit RDF valuetype enforced
            res2 = shacl.triples((s, self.convert_prefix("sh:nodeKind"), None))
        if res2 == "NA": # if no nodekind defined we assume Literal is fine.
            return Literal(value)
        for s,p,o in res2: 
            #print(s,p,o)
            if o == self.convert_prefix("sh:Literal"):
                return Literal(value)
            elif o == self.convert_prefix("sh:IRI"):
                if "http" in value: #HACK if the value is a valid URI (starts with http) make it a URIRef
                    return URIRef(value)
                else:
                    if self.debug:
                        Warning("Value {value} is not a valid URI, set to literal but should be removed or converted manually!")
                    return Literal(value)
            else:
                if self.debug:
                    Warning("Value {value} is a neither a Literal or a IRI")
                return Literal(value)
        if self.debug:
            Warning("{value} has passed throug all rdf datatype checks!")
        return Literal(value)
    

    def add_csv_catalog(self, csv, graph: Graph, node_id=None):
        """
        Extract catalog metadata from a sql view export and generate RDF following HRIv2 data model.
        This function expects there to be one (1) row in the csv.
        
        :param csv: path to a csv with ; delimitors and a header
        :type csv: str
        :param graph: The target graph where the catalog should be added
        :type graph: RDFLib Graph
        :param node_id: internal identifier for easier handling within the graph
        :type node_id: str
        """
        cat_table = pd.read_csv(csv,sep=";",header=0) # get data
        catalog = BNode(node_id)
        graph.add((catalog, RDF.type, DCAT.Catalog))
        graph.add((catalog, DCTERMS.title, Literal(cat_table.loc[:,"title_en"][0],lang="en")))
        graph.add((catalog, DCTERMS.title, Literal(cat_table.loc[:,"title_nl"][0],lang="nl")))
        graph.add((catalog, DCTERMS.description, Literal(cat_table.loc[:,"description_en"][0],lang="en")))
        graph.add((catalog, DCTERMS.description, Literal(cat_table.loc[:,"description_nl"][0],lang="nl")))
        contact_point = BNode(node_id + "/contactpoint")
        graph.add((contact_point, RDF.type, URIRef("http://www.w3.org/2006/vcard/ns#Kind")))
        graph.add((contact_point, URIRef("http://www.w3.org/2006/vcard/ns#hasEmail"), URIRef("mailto:" + cat_table.loc[:,"contactPoint_email"][0])))
        graph.add((contact_point, URIRef("http://www.w3.org/2006/vcard/ns#fn"), Literal(cat_table.loc[:,"contactPoint_name"][0],datatype=XSD.string)))
        graph.add((catalog, DCAT.contactPoint, contact_point))
        publisher = BNode(node_id + "/publisher")
        graph.add((publisher, RDF.type, FOAF.Agent))
        graph.add((publisher, FOAF.mbox, URIRef("mailto:" + cat_table.loc[:,"publisher_email"][0])))
        graph.add((publisher, DCTERMS.identifier, Literal(cat_table.loc[:,"publisher_identifier"][0])))
        graph.add((publisher, FOAF.name, Literal(cat_table.loc[:,"publisher_name_en"][0],lang="en")))
        graph.add((publisher, FOAF.name, Literal(cat_table.loc[:,"publisher_name_nl"][0],lang="nl")))
        graph.add((publisher, FOAF.homepage, URIRef(cat_table.loc[:,"publisher_url"][0])))
        graph.add((catalog, DCTERMS.publisher, publisher))

    
    def add_row_dataset(self, row, graph:Graph):
        """
        Extract all datasets from a SQL view export and generate RDF that corresponds to the HRIv2 model.

        :param csv: path to a csv with ; delimitors and a header
        :type csv: str
        :param graph: The target graph where the catalog should be added
        :type graph: RDFLib Graph
        """
        #dat_table = pd.read_csv(csv, sep=";",header=0) # get data
        dataset = BNode(row.loc["identifier"])
        graph.add((dataset, RDF.type, DCAT.Dataset))
        graph.add((dataset, DCTERMS.identifier, Literal(row.loc["identifier"])))
        graph.add((dataset, DCTERMS.title, Literal(row.loc["title_en"], datatype=XSD.string)))
        graph.add((dataset, DCTERMS.title, Literal(row.loc["title_nl"], datatype=XSD.string)))
        graph.add((dataset, DCTERMS.description, Literal(row.loc["description_en"], datatype=XSD.string)))
        graph.add((dataset, DCTERMS.description, Literal(row.loc["description_nl"], datatype=XSD.string)))
        graph.add((dataset, DCTERMS.accessRights, URIRef("http://publications.europa.eu/resource/authority/access-right/" + str(row.loc["accessRights"]))))
        graph.add((dataset, URIRef("http://data.europa.eu/r5r/applicableLegislation"), URIRef(row.loc["applicableLegislation"])))
        graph.add((dataset, URIRef("http://healthdataportal.eu/ns/health#numberOfRecords"), Literal(row.loc["numberOfRecords"],datatype=XSD.nonNegativeInteger)))
        graph.add((dataset, URIRef("http://healthdataportal.eu/ns/health#numberOfUniqueIndividuals"), Literal(row.loc["numberOfUniqueIndividuals"],datatype=XSD.nonNegativeInteger)))
        graph.add((dataset, DCAT.theme, URIRef("http://publications.europa.eu/resource/authority/data-theme/" + row.loc["theme"])))
        for keyword in row.loc["keywords"].split(","):
            graph.add((dataset, DCAT.keyword, Literal(keyword)))
        publisher = BNode(row.loc["publisher_identifier"] + "publisher")
        graph.add((publisher, RDF.type, FOAF.Agent))
        graph.add((publisher, FOAF.mbox, URIRef("mailto:" + row.loc["publisher_email"])))
        graph.add((publisher, DCTERMS.identifier, Literal(row.loc["publisher_identifier"])))
        graph.add((publisher, FOAF.name, Literal(row.loc["publisher_name_en"],lang="en")))
        graph.add((publisher, FOAF.name, Literal(row.loc["publisher_name_nl"],lang="nl")))
        graph.add((publisher, FOAF.homepage, URIRef(row.loc["publisher_url"])))
        graph.add((dataset, DCTERMS.publisher, publisher))
        creator = BNode(row.loc["creator_identifier"]+ "creator")
        graph.add((creator, RDF.type,  FOAF.Agent))
        graph.add((creator, FOAF.mbox, URIRef("mailto:" + row.loc["creator_email"])))
        graph.add((creator, FOAF.name, Literal(row.loc["creator_name"],datatype=XSD.string)))
        graph.add((creator, DCTERMS.identifier, Literal(row.loc["creator_identifier"])))
        graph.add((creator, FOAF.homepage, URIRef(row.loc["creator_url"])))
        graph.add((dataset, DCTERMS.creator, creator))
        contact_point = BNode()
        graph.add((contact_point, RDF.type, URIRef("http://www.w3.org/2006/vcard/ns#Kind")))
        graph.add((contact_point, URIRef("http://www.w3.org/2006/vcard/ns#hasEmail"), URIRef("mailto:" + row.loc["contactPoint_email"])))
        graph.add((contact_point, URIRef("http://www.w3.org/2006/vcard/ns#fn"), Literal(row.loc["contactPoint_name"],datatype=XSD.string)))
        graph.add((dataset, DCAT.contactPoint, contact_point))


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
    
    def _merge_desc(self, dataset, graph):
        """
        Merge all collected descriptions into a single string (xsd:string) required Health-RI v1 model.  

        :param dataset: dataset node id 
        :type dataset: str
        :param graph: graph containing dataset information
        :type graph: Graph
        """
        #TODO this function blindly merges strings, this could result in duplicate paragraphs in the FDP resource descriptions either the SOP for Mica has to change so dataset descriptions are fully autominous or we have to figure out a way to only select relevant descriptions.
        triples = graph.triples((dataset, DCTERMS.description, None)) # query graph for all descriptions associated to the new resource
        descriptions = ""
        for s, p, o in triples:
            descriptions = descriptions + "\n" + o
            graph.remove((s,p,o))
        graph.add((dataset, DCTERMS.description, Literal(descriptions, datatype=XSD.string))) #HACK Health-RI has currently forced descriptions to be xsd string value type
