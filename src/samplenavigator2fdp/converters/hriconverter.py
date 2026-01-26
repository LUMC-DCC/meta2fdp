import pandas as pd
from rdflib import Graph, BNode, RDF, Literal, URIRef, FOAF, DCAT, DCTERMS, XSD
from rdflib.namespace import Namespace
from sempyro.utils.validator_functions import force_literal_field
from samplenavigator2fdp.converters.abstractmodel import AbstractModel


from pydantic import AnyHttpUrl, Field, field_validator
import dateutil.parser as parser
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


# class FDPCatalog(HRICatalog):
#     is_part_of: [AnyHttpUrl] = Field(
#         description="Link to parent object", 
#         json_schema_extra={
#             "rdf_term": DCTERMS.isPartOf, 
#             "rdf_type": "uri"
#         })


class testconverter(AbstractModel):
    
    VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")

    def __init__(self, file_path,  class_map=None, debug=False):
        self.graph, self.prefix_map = self._prep_graph()
        self.file_path = file_path
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
    

    def sempyro_catalog(self, cat_table: pd.DataFrame, graph: Graph, url=None):
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


    def sempyro_dataset(self, row: pd.Series, graph:Graph, URI):
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
    
