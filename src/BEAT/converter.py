"""_summary_
Abstract class of a converter module. This class dictates input and
output of any converter class
"""
from rdflib import Graph, RDF, Literal, URIRef, DCTERMS, XSD, Namespace
from pandas import Series, DataFrame
from abc import ABCMeta, abstractmethod
from typing import List, Union
from sempyro import LiteralField
from sempyro.hri_dcat import (
    HRICatalog, 
    HRIDataset, 
    HRIVCard, 
    HRIAgent, 
    HRIDistribution,
    HRIDataService,
    HRIDatasetSeries
)


# TODO: factory function that generates a converter class based on available mappings:
# minimum information on mappings needed: fieldname/property, variable path, language
# mappping files are per resource

class Converter(metaclass=ABCMeta):

    def __init__(self,  class_map=None, debug=False):
        self.node_log = {}
        if class_map:
            self.class_map = class_map
        else:
            self.class_map = {'Project': "foaf:Project", 'Catalog': 'dcat:Catalog',
                               'Catalog_contactpoint': "vcard:Kind", 
                               'Catalog_publisher': "foaf:Agent", 
                               'Catalog_service': "dcat:DataService"}
        self.dataset_ids = []
        self.debug = debug
        self.VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")
        self.graph, self.prefix_map = self._prep_graph()

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
    
    def agent_rdf(self, metadata: Series) -> HRIAgent:
        return HRIAgent(
        name=[LiteralField(value=metadata.loc["publisher_name_en"], language="en"),
              LiteralField(value=metadata.loc["publisher_name_nl"], language="nl")],
        identifier=[metadata.loc["publisher_identifier"]],
        homepage=URIRef(metadata.loc["publisher_url"]),
        mbox="mailto:" + metadata.loc["publisher_email"],
        spatial = None,
        publisher_note=None,
        publisher_type=None
    )

    def vcard_rdf(self, metadata: Series) -> HRIVCard:
        vcard=HRIVCard(
        hasEmail="mailto:" + metadata.loc["contactPoint_email"],
        formatted_name=metadata.loc["contactPoint_name"]),
        return vcard


    def catalog_rdf(self, metadata: Series, creators: Union[list[HRIAgent], None], contact_point: HRIVCard, publisher: HRIAgent, service: Union[HRIDataService, None], url) -> HRICatalog:
        catalog = HRICatalog(
            title=[
                LiteralField(value=metadata.loc["title_en"], language="en"),
                LiteralField(value=metadata.loc["title_nl"], language="nl")
            ],
            description=[
                LiteralField(value=metadata.loc["description_en"], language="en"),
                LiteralField(value=metadata.loc["description_nl"], language="nl")
            ],
            creator=creators,
            contact_point=contact_point,
            publisher=publisher,
            service=service,
            dataset=[])
        self.graph.parse(data=catalog.to_graph(url).serialize())
        # print("debug")
        return catalog

    def sempyro_catalog(self, cat_table: DataFrame, graph: Graph, url=None):
        #Proof of concept function, needs to be reworked to be more flexible with input
        catalog = HRICatalog(
    title=[
        LiteralField(value=cat_table.loc["title_en"], language="en"),
        LiteralField(value=cat_table.loc["title_nl"], language="nl")
    ],
    description=[
        LiteralField(value=cat_table.loc["description_en"], language="en"),
        LiteralField(value=cat_table.loc["description_nl"], language="nl")
    ],
    contact_point=HRIVCard(
        hasEmail="mailto:" + cat_table.loc["contactPoint_email"],
        formatted_name=cat_table.loc["contactPoint_name"]),
    publisher=HRIAgent(
        name=[LiteralField(value=cat_table.loc["publisher_name_en"], language="en"),
              LiteralField(value=cat_table.loc["publisher_name_nl"], language="nl")],
        identifier=[cat_table.loc["publisher_identifier"]],
        homepage=URIRef(cat_table.loc["publisher_url"]),
        mbox="mailto:" + cat_table.loc["publisher_email"]
    ),
    dataset=[])
        graph.parse(data=catalog.to_graph(url).serialize())
        # print("debug")
        return url
    
    def sempyro_dataset(self, row: Series, graph:Graph, URI):
        dataset = HRIDataset(
        contact_point=HRIVCard(
            hasEmail=URIRef("mailto:" + row.loc["contactPoint_email"]),
            formatted_name=Literal(row.loc["contactPoint_name"]))
        ,
        creator=[HRIAgent( # identifier as object URI?
            name=[LiteralField(value=row.loc["creator_name"])], 
            identifier=[str(row.loc["creator_identifier"])],
            homepage= URIRef(row.loc["creator_url"]),
            mbox=URIRef("mailto:" + row.loc["creator_email"])    
        )],
        description=[LiteralField(value=row.loc["description_en"]),
                     LiteralField(value=row.loc["description_nl"])],
        #release_date=parser.isoparse("2024-07-01T11:11:11Z"),
        identifier=str(row.loc["identifier"]),
        #modification_date=parser.isoparse("2024-06-04T13:36:10Z"),
        publisher=HRIAgent( # identifier as object URI?
        name=[LiteralField(value=row.loc["publisher_name_en"], language="en"),
              LiteralField(value=row.loc["publisher_name_nl"], language="nl")],
        identifier=[str(row.loc["publisher_identifier"])],
        homepage=URIRef(row.loc["publisher_url"]),
        mbox="mailto:" + row.loc["publisher_email"]
        ),
        theme=[URIRef("http://publications.europa.eu/resource/authority/data-theme/" + row.loc["theme"])],
        title=[
        LiteralField(value=row.loc["title_en"]),
        LiteralField(value=row.loc["title_nl"])
        ],
        distribution=[],
        access_rights=URIRef("http://publications.europa.eu/resource/authority/access-right/" + str(row.loc["accessRights"])),
        keyword=row.loc["keywords"].split(","),
        applicable_legislation=[URIRef(row.loc["applicableLegislation"])],
        number_of_records=LiteralField(value=str(row.loc["numberOfRecords"]), datatype=XSD.nonNegativeInteger),
        number_of_unique_individuals=LiteralField(value=str(row.loc["numberOfUniqueIndividuals"]), datatype=XSD.nonNegativeInteger)
        )
        graph.parse(data=dataset.to_graph(URI + str(row.loc["identifier"])).serialize())
    

    @abstractmethod
    def dataset_rdf(self, metadata, graph: Graph) -> HRIDataset:
        raise NotImplemented


    @abstractmethod
    def distribution_rdf(self, metadata, graph: Graph) -> HRIDistribution:
        raise NotImplemented


    @abstractmethod
    def datasetseries_rdf(self, metadata, graph: Graph) -> HRIDatasetSeries:
        raise NotImplemented


    @abstractmethod
    def dataservice_rdf(self, metadata, graph: Graph) -> HRIDataService:
        raise NotImplemented


    def link_resource(self, subject, predicate, object, graph: Graph) -> None:
        """
        This function reads a graph, finds the
        subject and links it to the given object.

        :param subject: the uri associated with the subject node of the resource
        :type purl: URIRef
        :param predicate: predicate to assign
        :type predicate: URIRef
        :param object: the uri associated with the object node of the resource
        :type object: URIRef
        :param graph: Resource graph 
        :type graph: RDF Graph object
        """
        graph.add((subject, predicate, URIRef(object)))


    def subject_replace(self, PURL, node_id, dcat_type, graph) -> None:
        """
        Build a SPARQL CONSTRUCT query that replaces the object with the given
        DCAT type and run it on the given graph.

        :param PURL: new subject URI
        :type PURL: string
        :param node_id: original uri of object
        :type node_id: string
        :param dcat_type: RDFlib DCAT uri of the resource used as a tag on what object to replace
        :type dcat_type: RDFLib URIRef
        :param graph: graph to replace the main object from
        :type graph: RDFLib Graph
        """
        firstpart = """
        PREFIX dcat: <http://www.w3.org/ns/dcat#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX vcard: <http://www.w3.org/2006/vcard/ns#>

        CONSTRUCT {
        ?newResource ?p ?property .
        }
        WHERE {
        ?resource a <"""
        middle = """> ;
                    ?p ?property .
        BIND(<"""
        lastpart = """> AS ?newResource)
        }
        """
        q = firstpart + str(dcat_type) + middle + str(PURL) + lastpart
        qres = graph.query(q)
        for s, p, o in qres:
            graph.add((s,p,o))
        graph.remove((node_id, None, None))

    def _merge_desc(self, dataset, graph):
        """
        Merge all collected descriptions into a single string (xsd:string) required Health-RI v1 model.  

        :param dataset: dataset node id 
        :type dataset: str
        :param graph: graph containing dataset information
        :type graph: Graph
        """
        #TODO this function blindly merges strings, this could result in duplicate paragraphs in the FDP resource descriptions.
        #  either the SOP for Mica has to change so dataset descriptions are fully autominous or 
        # we have to figure out a way to only select relevant descriptions.
        triples = graph.triples((dataset, DCTERMS.description, None)) # query graph for all descriptions associated to the new resource
        descriptions = ""
        for s, p, o in triples:
            descriptions = descriptions + "\n" + o
            graph.remove((s,p,o))
        graph.add((dataset, DCTERMS.description, Literal(descriptions, datatype=XSD.string))) #HACK Health-RI has currently forced descriptions to be xsd string value type
    
    def get_dataset_nodes(self, graph:Graph) -> list:
        """
        Obtain blank node id's inside the graph

        :param graph:
        :type graph:
        :return:
        :rtype:
        """
        query = """PREFIX dcat: <http://www.w3.org/ns/dcat#> 
        SELECT ?s WHERE {
        ?s a dcat:Dataset
        }"""
        res = graph.query(query)
        return [id for id in res]