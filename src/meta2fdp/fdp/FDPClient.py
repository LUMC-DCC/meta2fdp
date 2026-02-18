"""
    Interface to interact FDP content
    source: https://github.com/Orphanet/orphadata-fdp-populator/blob/master/FDPClient.py
"""
from meta2fdp.fdp.abstractclient import AbstractClient
from typing import override
import requests
import json
from rdflib import Graph, RDF, URIRef, FOAF, DCAT, DCTERMS
from meta2fdp.graphutils.graphutils import graphutils
from keyring import get_password
from os import getenv

utils = graphutils()

class FDPClient(AbstractClient):

    def __init__(self, config) -> None:
        self.config = config
        self.URL = getenv(self.config["FDP"]["URL"])
        self.token = None
        self.parent_resource = self.config["FDP"]["parent_resource_purl"] if self.config["FDP"]["parent_resource_purl"] != "parent_resource_purl" else None
    
    @override
    def connection_status(self):
        """
        Basic function to check if connection to FDP is possible

        :param url: url to FDP
        :type url: String
        """
        try:
            response = requests.get(self.URL)
            if response.status_code == 200:
                if __debug__: 
                    print(f"Successfully connected to {self.URL}")
                return response.status_code
            else:
                print(f"Failed to connect to {self.URL}. Status code: {response.status_code}")
                return response.status_code
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to {self.URL}: {e}")

    @override
    def get_api_token(self):
        """
        This function generates an bearer-token:
        https://swagger.io/docs/specification/authentication/bearer-authentication/
        This is a token that can be used to authenticate your requests to the FDP server.
        This function returns a string

        :return: FDP API token
        :rtype: String
        """
        self.URL = getenv(self.config["FDP"]["URL"])
        self.token = get_password(self.URL, getenv(self.config["FDP"]["username"]))
        
        # Check if api-key works:
        url = self.URL + "/users/current"
        data = {}
        payload = json.dumps(data)
        headers = {
            'Content-Type': "application/json",
            'Authorization': "Bearer " + self.token
        }
        response = requests.request("get", url, data=payload, headers=headers)
        #print(response.text)
        if response.status_code == 200:
            pass
        elif response.status_code == 401:
            raise ConnectionRefusedError("API Token has no Authorization! Check the pipeline config FDP attributes if correct environment variables are assiged")
        elif response.status_code == 403:
            raise ConnectionRefusedError("API Token is forbidden to see current user data! Check the pipeline config FDP attributes if correct environment variables are assiged")
        else:
            raise ConnectionRefusedError(f"API-key doesn't work, error: {response.json()["text"]["error"]}")
    
    
    
    @override
    def get_resource(self, url):
        """
        This function obtains resource metadata  
        
        :param url: URL of resource metadata
        :type url: String
        :return: response body
        :rtype: String
        """
        data = {}
        
        payload = json.dumps(data)

        headers = {
            'Content-Type': "text/turtle",
            'Authorization': "Bearer " + self.token
        }

        response = requests.request("GET", url, data=payload, headers=headers)
        
        body = response.text

        return body

    @override
    def post_resource(self, data, resource_type):
        """
        This function is used to upload resource metadata onto a FDP server.

        :param data: A string containing a turtle formatted RDF description of a resource
        :type data: String
        :param resource_type: A string, in current context: "catalog" or "dataset" or "distribution"
        :type resource_type: String
        :return: A string containing a persistent url of the uploaded resource description.
        :rtype: String
        """
        #print(data)
        # merge server url with resource type to define the resource for the server
        url = self.URL + "/" + resource_type
        headers = {
            'Content-Type': "text/turtle",
            'Authorization': "Bearer " + self.token
        } # change Content-Type to work with other formatting
        if not isinstance(data, str): # make sure the resource description is a string or change it into a string if not
            data = data.decode("utf-8")
        # upload resource description
        response = requests.request("POST", url, data=data.encode('utf-8'), headers=headers)
        # TODO: make this a verbose mode
        if True:
            print(response.status_code) #check server response
            print(response.headers)
            print(response.text)
            print(response.content)
        try:
            resource_url = response.headers["Location"]
        except KeyError:
            raise FileNotFoundError("Error getting location url, if this is because of badly formed metadata this is the SHACL validation report:\n {}".format(response.text))
        #print(resource_url)
        # self.publish_metadata(resource_url.replace(self.FDP_P_URL, self.FDP_URL + "/")) # replace the FDP server URL with the persistent URL of the resource

        return resource_url

    @override
    def publish_resource(self, url):
        """
        This function sends the FDP server a command to publish a resource description.

        :param url: A string containing the url linking tot the resource description on the FDP
        :type url: String
        """
        # extend the url to point to the publication state attribute of the resource description
        state_url = url + "/meta/state" 
        # Define the resource description as published
        data = {"current": "PUBLISHED"}

        headers = {
            'Content-Type': "application/json",
            'Authorization': "Bearer " + self.token
        }

        payload = json.dumps(data)
        response = requests.request("PUT", state_url, data=payload, headers=headers)
        # check server response (manual)
        if __debug__:
            print(response.status_code)
            print(response.headers)
            print(response.text)

    @override
    def put_resource(self, resource_url, body):
        """
        Update content of a given resource description.
        
        :param resource_url: A string containing the url linking tot the resource description on the FDP
        :type resource_url: String
        :param body: A string containing a turtle formatted RDF that changes the resource
        :type body: String
        """
        headers = {
            'Content-Type': 'text/turtle',
            'Authorization': "Bearer " + self.token,
            'Origin': self.URL,
            'Referer': resource_url + "/edit"
        }
        response = requests.request("PUT", resource_url, data=body.encode("utf-8"), headers=headers)
        if self.verbose:
            print(response)
        return response

    @override
    def upload_resource(self, graph, purl, resource_type="Catalog", resource_name="Catalog"):
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
        data = self.link_resource(graph, purl, resource_type)
        resource_url = self.upload_data(data, resource_name)
        return resource_url

    @override
    def get_children(self, graph: Graph):
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


    def get_resource_id(self, dcat_type, graph):
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

    SELECT ?o WHERE {
        ?s dcterms:identifier ?o ;
            a <""" + str(dcat_type) + """> .
    }
    """
        )
        if len(qres.bindings) == 1:
            return qres.bindings.pop()['o']
        elif len(qres.bindings) == 0:
            return qres #TODO make unified return type
        else:
            LookupError("multiple identifiers found, are you sure this is a unique resource?")


    def remove_blank_node(self, node_triples, graph):
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


    def update_resource(self, url, dcat_type, new_graph: Graph):
        """
        Update resource with new content. To ensure PUT requests
        succeeds, we get the current content on the FDP and
        replace all values that are in the new_graph within the
        FDP_graph.
        We use the dcat_type to extract the main subject
        as there should only be one resource with the type
        in the graph.

        :param url: the url of the FDP resource that should be able to handle requests
        :type url: str
        :param dcat_type: RDFLib DCAT resource type URIRef
        :type dcat_type: RDFLib DCAT resource type URIRef
        :param new_graph: Graph with new content
        :type new_graph: RDFLib Graph
        :return: updated FDP resource rdf graph
        :rtype: RDFLib Graph
        """
        content = self.get_metadata(url)
        FDP_graph = Graph().parse(data=content)
        #set_changes(new_graph, FDP_graph)

        new_id = self.get_resource_id(dcat_type, new_graph) 
        FDP_id = self.get_resource_id(dcat_type, FDP_graph)
        if new_id != FDP_id: #HACK IF THE RESOURCE HAS NO DCTERMS:IDENTIFIER IT WILL AUTOMATICALLY MATCH
            raise IndexError("resource id {} does not match with current update!".format(url))
        else:
            #assume that object is fdp/new URL
            utils.subject_replace(url, node_id=self.URL + "/" + "new", dcat_type=dcat_type, graph=new_graph)
            #print(FDP_graph.serialize())
            old_agents = [triple for triple in FDP_graph.triples((None, RDF.type, FOAF.Agent))]
            old_Kinds = [triple for triple in FDP_graph.triples((None, RDF.type, URIRef("http://www.w3.org/2006/vcard/ns#Kind")))]

            for triple in new_graph.triples((None, None, None)):
                FDP_graph.set(triple)
            self.remove_blank_node(old_agents, FDP_graph)
            self.remove_blank_node(old_Kinds, FDP_graph)
            #print(FDP_graph.serialize())
            self.update_metadata(url, FDP_graph.serialize())
        return FDP_graph


    def get_dataset_id_purls(self, graph: Graph) -> dict:  #FIXME update based on content in replace_datasets in csvparser
        """
        Get all dataset URL's and dcterm:identifiers for a given catalog
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
            metadata = self.get_metadata(purl_string)
            if metadata == "You are not allow to view this record in state DRAFT":
                continue # skip draft datasets
            dataset_metadata = Graph().parse(data=metadata)
            dataset_id = self.get_resource_id(DCAT.Dataset, dataset_metadata)
            datasets[dataset_id] = purl[0]
        # first get the dataset purls
        # then do GET request to see content of datasets
        # extract the identifier from datasets
        # return identifier: purl dictionary
        return datasets
    
    def update_catalog(self, catalog_purl, graph):
        #TODO remove
        """
        Update a given catalog and get the child datasets
        of the given catalog for further update.
        :param catalog_purl: url associated with the FDP to update
        :type catalog_purl: str
        :param graph: new catalog metadata content
        :type graph: RDFLib Graph
        """
        ## debug reporter
        #parser.graph.set((URIRef(URL + "/" + "new"), DCTERMS.description , Literal("check check"))) 
        catalog_graph = self.update_resource(catalog_purl, DCAT.Catalog, graph)
        return catalog_graph

    def get_dataset_nodes(self, graph:Graph) -> list:
        #TODO make generic
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