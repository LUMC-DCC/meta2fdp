"""
    Interface to interact FDP content
    source: https://github.com/Orphanet/orphadata-fdp-populator/blob/master/FDPClient.py
"""
import requests
import json
from rdflib import Graph, RDF, URIRef, FOAF, DCAT, DCTERMS

from pathlib import Path
import sys
path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))
from graphutils import *


class FDPClient:
    """
    Interface to interact FDP content
    source: https://github.com/Orphanet/orphadata-fdp-populator/blob/master/FDPClient.py
    """

    # The main URL of the FDP server
    URL = "https://example-fdp.nl"
    # username of an FDP admin
    FDP_ADMIN_USERNAME = "albert.einstein@example.com" 
    # password of an FDP admin
    FDP_ADMIN_PASSWORD = "password" 
    # this is the URL of the parent resource
    PURL = "https://example-fdp.nl/catalog/ac5d6134-6b7b-4989-80dd-5b1714023e3d" 

    def __init__(self, fdp_url, username, password, persistent_url, verbose=True):
        self.URL = fdp_url # this is the main URL of the FDP server
        self.FDP_ADMIN_USERNAME = username
        self.FDP_ADMIN_PASSWORD = password
        self.PURL = persistent_url # this is the URL of the parent resource
        self.verbose = verbose

    def check_url(self, url):
        """
        Basic function to check if connection to FDP is possible

        :param url: url to FDP
        :type url: String
        """
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print(f"Successfully connected to {url}")
            else:
                print(f"Failed to connect to {url}. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to {url}: {e}")


    def fdp_get_token(self):
        """
        This function generates an bearer-token:
        https://swagger.io/docs/specification/authentication/bearer-authentication/
        This is a token that can be used to authenticate your PUT and POST requests to the FDP server.
        This function returns a string

        :return: FDP API token
        :rtype: String
        """
        url = self.URL + "/tokens"

        data = {"email": self.FDP_ADMIN_USERNAME, "password": self.FDP_ADMIN_PASSWORD}

        payload = json.dumps(data)

        headers = {
            'Content-Type': "application/json"
        }

        response = requests.request("POST", url, data=payload, headers=headers)
        #print(response.text)
        data = json.loads(response.text)

        return data["token"]
    
    def get_metadata(self, url):
        """
        This function obtains resource metadata  
        
        :param url: URL of resource metadata
        :type url: String
        :return: response body
        :rtype: String
        """
        data = {"email": self.FDP_ADMIN_USERNAME, "password": self.FDP_ADMIN_PASSWORD}
        
        payload = json.dumps(data)

        headers = {
            'Content-Type': "text/turtle"
        }

        response = requests.request("GET", url, data=payload, headers=headers)
        
        body = response.text

        return body

    def create_metadata(self, data, resource_type):
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
        token = self.fdp_get_token() # log in
        authorization = "Bearer " + token
        headers = {
            'Content-Type': "text/turtle",
            'Authorization': authorization
        } # change Content-Type to work with other formatting
        if not isinstance(data, str): # make sure the resource description is a string or change it into a string if not
            data = data.decode("utf-8")
        # upload resource description
        response = requests.request("POST", url, data=data.encode('utf-8'), headers=headers)
        # TODO: make this a verbose mode
        if self.verbose:
            print(response.status_code) #check server response
            print(response.headers)
            print(response.text)
            print(response.content)
        # FIXME this already throws an error:
        #resource_url = response.headers["Location"] # get the FDP server URL of the new resource description
        try:
            resource_url = response.headers["Location"]
        except KeyError:
            raise FileNotFoundError("Error getting location url, if this is because of badly formed metadata this is the SHACL validation report:\n {}".format(response.text))
        #print(resource_url)
        # self.publish_metadata(resource_url.replace(self.FDP_P_URL, self.FDP_URL + "/")) # replace the FDP server URL with the persistent URL of the resource

        return resource_url

    def publish_metadata(self, url):
        """
        This function sends the FDP server a command to publish a resource description.

        :param url: A string containing the url linking tot the resource description on the FDP
        :type url: String
        """
        token = self.fdp_get_token() # log in
        authorization = "Bearer " + token
        # extend the url to point to the publication state attribute of the resource description
        state_url = url + "/meta/state" 
        # Define the resource description as published
        data = {"current": "PUBLISHED"}

        headers = {
            'Content-Type': "application/json",
            'Authorization': authorization
        }

        payload = json.dumps(data)
        response = requests.request("PUT", state_url, data=payload, headers=headers)
        # check server response (manual)
        if self.verbose:
            print(response.status_code)
            print(response.headers)
            print(response.text)

    def update_metadata(self, resource_url, body):
        """
        Update content of a given resource description.
        
        :param resource_url: A string containing the url linking tot the resource description on the FDP
        :type resource_url: String
        :param body: A string containing a turtle formatted RDF that changes the resource
        :type body: String
        """
        token = self.fdp_get_token()
        headers = {
            'Content-Type': 'text/turtle',
            'Authorization': 'Bearer {}'.format(token),
            'Origin': 'https://fdp.example.org',
            'Referer': resource_url + "/edit"
        }
        response = requests.request("PUT", resource_url, data=body.encode("utf-8"), headers=headers)
        if self.verbose:
            print(response)
        return response
    
    def upload_data(self, data, resource_name="Catalog"):
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
            response = self.create_metadata(data, resource_name)
        else:
            response = self.create_metadata(data, resource_name.lower())
        return response


    def link_resource(self, graph, purl, resource_type):
        """
        This function reads a graph, finds the
        target resource and links it to the given
        parent resource. This should be a parent
        resource in the target FDP.

        :param graph: Resource graph 
        :type graph: RDF Graph object
        :param purl: the permament url associated with the parent node of the resource
        :type purl: URIRef
        :param resource_type: dcat resouce type
        :type resource_type: String
        :return: linked resource graph Turtle serialization
        :rtype: String
        """
        print(graph.serialize())
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
        #print(data)
        resource_url = self.upload_data(data, resource_name)
        #print(resource_url)
        # time.sleep(5) # sleep to make sure that the server has time handle the POST request
        # self.publish_metadata(resource_url)
        #self.update_metadata(resource_url, test_body)
        return resource_url


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

        :param url: the url of the FDP that should be able to handle requests
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
            subject_replace(url, node_id=self.PURL + "new", dcat_type=dcat_type, graph=new_graph)
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
        """
        Update a given catalog and get the child datasets
        of the given catalog for further update.
        :param catalog_purl: url associated with the FDP to update
        :type catalog_purl: str
        :param graph: new catalog metadata content
        :type graph: RDFLib Graph
        """
        #parser.graph.set((URIRef(PURL + "new"), DCTERMS.description , Literal("check check"))) #HACK debug reporter
        catalog_graph = self.update_resource(catalog_purl, DCAT.Catalog, graph)
        return catalog_graph

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