from rdflib import URIRef, DCTERMS, BNode, Literal, XSD, DCAT, Graph, Dataset, RDF, FOAF
from rdflib.plugins.sparql import prepareUpdate
from hriconverter import HealthRIConverterv2
from pathlib import Path
import sys
path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))

from fdp.FDPClient import FDPClient
from os import getenv
import yaml
import json
from datetime import datetime
import pandas as pd
import keyring
from pymssql import connect

conf_path = getenv("CONF_PATH", default="config/configuration.yaml")

# get default values from config file
with open(conf_path, "r") as config_file:
    config = yaml.safe_load(config_file)

cred_path = getenv("CRED_PATH", default=config["file_paths"]["credentials"])

def connect_client(cred_path):
    ### set up connection settings to FDP server ###
    URL = URIRef(config["FDP"]["URL"])
    PURL = URIRef(config["FDP"]["PURL"])
    with open(cred_path, 'r') as infile:
        credentials = json.load(infile)
    client = FDPClient(URL, credentials["username"], credentials["password"], PURL)
    # ping server:
    #client.check_url(URL)
    return URL, PURL, client

URL, PURL, client = connect_client(cred_path)
catalog_file_path = config["file_paths"]["catalog_input_file"]
datasets_file_path = config["file_paths"]["datasets_input_file"]
catalog_shacl_path = config["file_paths"]["catalog_shacl"]
dataset_shacl_path = config["file_paths"]["dataset_shacl"]

def upload_data(data, resource_name="Catalog"):
    """
    Use the FDPClient to upload metadata.

    :param data: FDP resource
    :type data: rdflib Graph object
    :param resource_name: Name of the resource, this should be the one that is used in the resource profile on the FDP
    :type resource_name: String
    :return: FDP api response containing resource URL
    :rtype: String
    """
    #added .lower to make sure the code works with the resource URL used by the LUMC FDP
    if resource_name == "DatasetSeries" or resource_name == "Network" or resource_name == "Population":
        response = client.create_metadata(data, resource_name)
    else:
        response = client.create_metadata(data, resource_name.lower())
    return response


def link_resource(graph, purl, resource_type):
    """
    This function reads an RDF file, finds the
    target resource and links it to the given
    parent resource. This should be a parent
    resource in the target FDP.

    :param graph: Resource graph 
    :type graph: RDF Graph object
    :param purl: the permament url associated with the parent node of the resource
    :type purl: URIRef
    :param resource_type: dcat resouce type
    :type resource_type: String
    :return: linked resource graph
    :rtype: RDF Graph object
    """
    res = graph.query("SELECT ?s WHERE {?s ?p <" +  str(resource_type) +  "> . } ") #TODO make this work for multiple resource definitions.
    x = 0
    for s in res:
        subject = s[0]
        x += 1
    if x > 1:
        raise Exception("multiple class instances of {}".format(resource_type))
    if x == 0:
        raise Exception(
            "could not find class {} in graph".format(resource_type)
        )
    graph.add((subject, DCTERMS.isPartOf, URIRef(purl)))
    # print("debug link resource")
    # print(graph.serialize())
    return graph.serialize() 


def upload_resource(graph, purl, resource_type="Catalog", resource_name="Catalog"):
    """
    This function takes links the current FDP resource to it's parent node,
    POST's the data and Publishes the data
    
    :param graph: Resource graph 
    :type graph: RDF Graph object
    :param purl: Persistent URL of parent node !!!!NO / at the end!!!!
    :type purl: String
    :param resource_type: dcat resouce type, this should match the metadata schema name on the FDP
    :type resource_type: String
    :param resource_name: Name of the resource, this should be the one that is used in the resource profile on the FDP
    :type resource_name: String
    :return: Permanent URL of resource
    :rtype: String
    """
    data = link_resource(graph, purl, resource_type)
    #print(data)
    resource_url = upload_data(data, resource_name)
    #print(resource_url)
    # time.sleep(5) # sleep to make sure that the server has time handle the POST request
    # client.publish_metadata(resource_url)
    #client.update_metadata(resource_url, test_body)
    return resource_url


def object_replace(PURL, node_id, dcat_type, graph):
    """
    Build a SPARQL CONSTRUCT query that replaces the object with the given
    DCAT type and run it on the given graph.

    :param PURL: new object URI
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


def match_id(identifier: str, graph: Graph):
    """
    Builds a SPARQL ASK query, that checks if a identifier exists,
    and run it on the given graph. This done to check if an
    object exists with the given identifier.

    :param identifier: identifier that should exist
    :type identifier: str
    :param graph: graph to query 
    :type graph: RDFLIB Graph
    :return: query result
    :rtype: Boolean
    """
    qres = graph.query(
        """
PREFIX dcterms: <http://purl.org/dc/terms/>

ASK WHERE {
     ?s dcterms:identifier \"""" + identifier + """\" .
}
"""
    )
    return qres.askAnswer


def get_children(graph: Graph):
    """
    Obtain child nodes of FDP resource.
    
    :param graph: A graph to query
    :type graph: RDFLib Graph
    :return: query result
    :rtype: QueryResult Object
    """
    qres = graph.query(
        """SELECT ?o WHERE {
?s ?p ?o .
FILTER (?p = <http://www.w3.org/ns/ldp#contains>)
}
"""
    )
    return qres


def get_resource_id(dcat_type, graph):
    #TODO unify return
    """
    Obtain the id of a specific dcat resource type.
    This function handles three different cases:
    If there is exactly one identifier it returns
    the 
    :param dcat_type:
    :type dcat_type:
    :param graph:
    :type graph:
    :return:
    :rtype:
    """
    qres = graph.query(
        """
PREFIX dcterms: <http://purl.org/dc/terms/>

SELECT ?s WHERE {
    ?o dcterms:identifier ?s ;
        a <""" + str(dcat_type) + """> .
}
"""
    )
    if len(qres.bindings) == 1:
        return qres.bindings.pop()['s']
    elif len(qres.bindings) == 0:
        return qres #TODO make unified return type
    else:
        LookupError("multiple identifiers found, are you sure this is a unique resource?")


def set_changes(new_graph, old_graph):
    """
    """
    merge_environment = Dataset()
    print(merge_environment.store)
    merge_environment.get_context("http://example.org/new_graph").parse(data=new_graph.serialize())
    merge_environment.get_context("http://example.org/old_graph").parse(data=old_graph.serialize())
    merge_query = "PREFIX ex: http://example.org/ \
    WITH ex:old_graph DELETE {  ?s ?p ?oldObject ;  ?oldObject ?pobject ?oldObjvalue .} INSERT {  ?s ?p ?newObject ;  ?newObject ?pobject ?newvalue .} WHERE {  GRAPH ex:new_graph {    ?s ?p ?oldObject ;    ?oldObject ?pobject ?newvalue .  }}"
    test = prepareUpdate(str(merge_query)) #doesn't work, maybe try a different triplestore/Memory?
    print(merge_environment.graph("http://example.org/old_graph"))


def remove_blank_node(node_triples, graph):
    """
    Remove all associated triples to a blank node within
    the given graph.
    :param node_triples: a list of triples where the object is a blank node
    :type node_triples: list
    :param graph: graph that has the blank nodes
    :type graph: RDFLib Graph
    """
    for node_triple in node_triples:
        for triple in graph.triples((node_triple[0], None, None)):
            graph.remove(triple)


def update_resource(url, dcat_type, new_graph: Graph):
    """
    Update resource with new content. To ensure PUT requests
    succeeds, we get the current content on the FDP and
    replace all values that are in the new_graph within the
    FDP_graph.
    :param url: the url of the FDP that should be able to handle requests
    :type url: str
    :param dcat_type: RDFLib DCAT resource type URIRef
    :type dcat_type: RDFLib DCAT resource type URIRef
    :param new_graph: Graph with new content
    :type new_graph: RDFLib Graph
    :return: updated FDP resource rdf graph
    :rtype: RDFLib Graph
    """
    content = client.get_metadata(url)
    FDP_graph = Graph().parse(data=content)
    #set_changes(new_graph, FDP_graph)

    new_id = get_resource_id(dcat_type, new_graph)
    FDP_id = get_resource_id(dcat_type, FDP_graph)
    if new_id != FDP_id:
        IndexError("resource id {} does not match with current update!".format(url))
    else:
        #assume that object is fdp/new URL
        object_replace(url, node_id=PURL + "new", dcat_type=dcat_type, graph=new_graph)
        print(FDP_graph.serialize())
        old_agents = [triple for triple in FDP_graph.triples((None, RDF.type, FOAF.Agent))]
        old_Kinds = [triple for triple in FDP_graph.triples((None, RDF.type, URIRef("http://www.w3.org/2006/vcard/ns#Kind")))]

        for triple in new_graph.triples((None, None, None)):
            FDP_graph.set(triple)
        remove_blank_node(old_agents, FDP_graph)
        remove_blank_node(old_Kinds, FDP_graph)
        print(FDP_graph.serialize())
        client.update_metadata(url, FDP_graph.serialize())
    return FDP_graph


def get_dataset_id_purls(graph):
    """
    Get all datasets for a given catalog
    first get the dataset purls
    then do GET request to see content of datasets
    extract the identifier from datasets
    return identifier: purl dictionary
    :param graph: a graph containing a FDP catalog resource
    :type graph: RDFLib Graph
    :return: dictionary with key=dataset identifier: value=purl
    :rtype: dict
    """
    purl_req = """PREFIX ldp: <http://www.w3.org/ns/ldp#>
    SELECT ?o WHERE{
     ?s ldp:contains ?o .}
    """
    result = graph.query(purl_req)
    datasets = {}
    for purl in result:
        purl_string = str(purl[0])
        metadata = client.get_metadata(purl_string)
        if metadata == "You are not allow to view this record in state DRAFT":
            continue # skip draft datasets
        dataset_metadata = Graph().parse(data=metadata)
        dataset_id = get_resource_id(DCAT.Dataset, dataset_metadata)
        datasets[dataset_id] = purl[0]
    # first get the dataset purls
    # then do GET request to see content of datasets
    # extract the identifier from datasets
    # return identifier: purl dictionary
    return datasets

def update_catalog(catalog_purl, graph):
    """
    Update a given catalog and get the child datasets
    of the given catalog for further update.
    :param catalog_purl: url associated with the FDP to update
    :type catalog_purl: str
    :param graph: new catalog metadata content
    :type graph: RDFLib Graph
    :return:  dictionary with key=dataset identifier: value=purl
    :rtype: dict
    """
    #parser.graph.set((URIRef(PURL + "new"), DCTERMS.description , Literal("check check"))) #HACK debug reporter
    catalog_graph = update_resource(catalog_purl, DCAT.Catalog, graph) #HACK should make a seperate function to do this
    datasets = get_dataset_id_purls(catalog_graph)
    return datasets

def get_dataset_nodes(graph:Graph) -> list:
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


#file_path = "data/BEAT/Health-RI Core Metadata model v2 filled BEAT.xlsx"
#file_path = "data/BEAT/Health-RI Core Metadata model v2 filled Comodulate.xlsx"

parser = HealthRIConverterv2(catalog_file_path)

input_format = config["mode"]["input_format"]

if input_format == "Excel":
    parser.parse_catalog(shacl=catalog_shacl_path)
    object_replace(PURL + "new", BNode("Catalog"), DCAT.Catalog, parser.graph)
    if config["mode"]["replace"] == True:
        catalog_purl = config["FDP"]["catalog_purl"]
        datasets = update_catalog(catalog_purl, parser.graph)
    else:
        catalog_purl = upload_resource(parser.graph, URL, resource_type=DCAT.Catalog)
    print("datasets")
    parser.parse_dataset(datasets_file_path, shacl=dataset_shacl_path)
    catalog_description = next(parser.graph.triples((None, DCTERMS.description, None)))
    
    for dataset_node_id in parser.dataset_ids:
        dataset = parser.graph.cbd(BNode(dataset_node_id))
        dataset.remove((BNode(dataset_node_id), DCTERMS.isReferencedBy, Literal("Links to BEAT publications:")))
        dataset.remove((BNode(dataset_node_id), DCTERMS.isReferencedBy, Literal("Links to BEAT publications")))
        if catalog_file_path == "data/BEAT/Health-RI Core Metadata model v2 filled BEAT.xlsx":
            dataset.add((BNode(dataset_node_id), DCTERMS.issued, Literal(datetime(year=2024,month=2, day=4).isoformat(), datatype=XSD.dateTime)))
            dataset.add((BNode(dataset_node_id), DCTERMS.modified, Literal(datetime(year=2024,month=2, day=4).isoformat(), datatype=XSD.dateTime)))
        elif catalog_file_path == "data/BEAT/Health-RI Core Metadata model v2 filled Comodulate.xlsx":
            dataset.add((BNode(dataset_node_id), DCTERMS.issued, Literal(datetime(year=2025,month=4, day=4).isoformat(), datatype=XSD.dateTime)))
            dataset.add((BNode(dataset_node_id), DCTERMS.modified, Literal(datetime(year=2025,month=4, day=4).isoformat(), datatype=XSD.dateTime)))
        dataset.add((BNode(dataset_node_id), DCTERMS.license, URIRef(config["default_values_metadata"]["license"])))
        dataset.add((BNode(dataset_node_id), URIRef("http://data.europa.eu/r5r/applicableLegislation")  , URIRef("http://data.europa.eu/eli/reg/2025/327/oj")))
        # add catalog description:
        dataset.add((BNode(dataset_node_id), DCTERMS.description, catalog_description[2]))
        parser._merge_desc(BNode(dataset_node_id), dataset)
        object_replace(PURL + "new", BNode(dataset_node_id), DCAT.Dataset, dataset) # replace mode also assumes FDP resource PURL
        if config["mode"]["replace"] == True:
            try:
                dataset_identifier = dataset.value(subject=URIRef(PURL + "new"), predicate=DCTERMS.identifier)
                matching_purl = datasets[dataset_identifier]
                update_resource(matching_purl, DCAT.Dataset, dataset)
            except KeyError:
                Warning("Missing dataset on FDP! {dataset_identifier} \n uploading new dataset")
                resource_string = link_resource(dataset, catalog_purl, DCAT.Dataset)
                upload_data(dataset.serialize(), "Dataset")
        else:
            resource_string = link_resource(dataset, catalog_purl, DCAT.Dataset)
            upload_data(dataset.serialize(), "Dataset")
elif input_format == "csv":
    parser.add_csv_catalog(pd.read_csv(catalog_file_path,sep=";",header=0), parser.graph, "Catalog")
    object_replace(PURL + "new", BNode("Catalog"), DCAT.Catalog, parser.graph)
    catalog_purl = upload_resource(parser.graph, URL, resource_type=DCAT.Catalog, resource_name="Catalog")
    if config["mode"]["replace"] == True:
        catalog_purl = config["FDP"]["catalog_purl"]
        datasets = update_catalog(catalog_purl, parser.graph)
    else:
        catalog_purl = upload_resource(parser.graph, URL, resource_type=DCAT.Catalog)
    print("datasets")
    dat_table = pd.read_csv(datasets_file_path, sep=";",header=0)
    parser.add_row_dataset(dat_table, parser.graph) # TODO ADD AGENT IDENTIFIER AS BLANK NODE ID
    dataset_list = get_dataset_nodes(parser.graph)
    for node_id in dataset_list:
        dataset_graph = parser.graph.cbd(node_id[0])
        object_replace(PURL + "new", node_id[0], DCAT.Dataset, dataset_graph)
        dataset_graph.remove((BNode(node_id[0]), None, None))
        link_resource(dataset_graph, catalog_purl, DCAT.Dataset)
        upload_resource(dataset_graph, catalog_purl, resource_type=DCAT.Dataset, resource_name="Dataset")
elif input_format == "SQL":
    conn = connect(server=config["SQL"]["server_name"],user=config["SQL"]["username"],password=keyring.get_password(service_name=config["SQL"]["keyring_service"], username=config["SQL"]["username"]), database=config["SQL"]["database_name"],tds_version="7.4")
    parser.add_csv_catalog()
        