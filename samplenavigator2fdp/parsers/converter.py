"""Originally a complete Abstract class of a converter module. A class that dictates input and
output of any converter class. 
But it has slowly grown into a parent class for converting metadata to RDF through different functions.
"""
from rdflib import Graph, Literal, URIRef, DCTERMS, XSD, Namespace
from pandas import Series
from abc import ABCMeta, abstractmethod
from typing import  Union
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


    def catalog_rdf(self, metadata: Series, creators: Union[list[HRIAgent], None], contact_point: HRIVCard, publisher: HRIAgent, service: Union[HRIDataService, None], url: URIRef) -> HRICatalog:
        """This a more generic sempyro catalog constructor that tries to build towards a more flexible
        generation of catalogs. The main point of doing this is to seperate different classes into their own functions.
        

        :param metadata: The metadata of a catalog
        :type metadata: Series
        :param creators: A catalog can have 0 or more creators, which are a described as agents
        :type creators: Union[list[HRIAgent], None]
        :param contact_point: A catalog has one contactpoint (for now) and is described with a Vcard
        :type contact_point: HRIVCard
        :param publisher: Publisher should be LUMC, see configuration for default values that could be used.
        :type publisher: HRIAgent
        :param service: Possible dataservice where distribution access is serviced.
        :type service: Union[HRIDataService, None]
        :param url: Subject url / internal URL to be used to represtent the catalog
        :type url: URIRef
        :return: Catalog class for reuse or manipulation
        :rtype: HRICatalog
        """
        # TODO switch creators to attributions (creators are specifically creators of the catalog e.g. LUMC not the authors of a study)
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
        self.graph.parse(data=catalog.to_graph(url).serialize())  # put catalog into local graph
        # print("debug")
        return catalog

    def sempyro_catalog(self, cat_table: Series, graph: Graph, url=None):
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
        identifier= URI + str(row.loc["identifier"])
        graph.parse(data=dataset.to_graph(identifier).serialize())
        self.dataset_ids.append(identifier)
        return identifier
    

    #@abstractmethod
    #def dataset_rdf(self, metadata, graph: Graph) -> HRIDataset:
    #    raise NotImplemented


    #@abstractmethod
    #def distribution_rdf(self, metadata, graph: Graph) -> HRIDistribution:
    #    raise NotImplemented


    #@abstractmethod
    #def datasetseries_rdf(self, metadata, graph: Graph) -> HRIDatasetSeries:
    #    raise NotImplemented


    #@abstractmethod
    #def dataservice_rdf(self, metadata, graph: Graph) -> HRIDataService:
    #    raise NotImplemented


    