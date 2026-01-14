from abc import ABCMeta, abstractmethod
from rdflib import Graph, URIRef
from typing import Iterator

class Client(metaclass=ABCMeta):

    def __init__(self) -> None:
        self.URL = None
        self.token = None #Only store token 
    
    def connection_status(self) -> int:
        """Basic function to check if connection to a FDP is possible

        :return: server response status code
        :rtype: int
        """

    def get_api_token(self) -> str:
        """
        This function generates an bearer-token:
        https://swagger.io/docs/specification/authentication/bearer-authentication/
        This is a token that can be used to authenticate your requests to the FDP server. The password should be aquired through a keyring service.

        :return: FDP API token
        :rtype: String
        """

    def get_resource(self, url: str) -> str:
        """Get the metadata of a resource from the content of a location
        on the FDP.

        :param url: URL to resource
        :type url: str
        :return: _description_
        :rtype: str
        """
        # decision: always output str or Graph? should both options have a function?
    
    def post_resource(self, resource_ttl: str, resource_type: str) -> str:
        """Post a new resource description of a specific type to FDP.
        

        :param resoure_ttl: A graph serialized in the ttl format
        :type resoure_ttl: str
        :param resource_type: The resource type/class name on the FDP,
        this is case sensitive and will be used in the requests in this way: <https://fdp.org/RESOURCE_TYPE>
        :type resource_type: str
        :return: Location of the new resource on the FDP ie URL
        :rtype: str
        """
    

    def put_resource(self, resource_ttl: Graph, resource_url: URIRef, resource_type: str):
        """Put completely new resource description of a specific type to an existing
        resource location on the FDP.

        :param resource_ttl: A graph serialized in the ttl format it should
        contain the triples that are automatically added to the resource description
        by the FDP
        :type resource_ttl: Graph
        :param resource_url: The URL of the existing resource location on the FDP
        :type resource_url: URIRef
        :param resource_type: The resource type/class name on the FDP,
        this is case sensitive and will be used in the requests in this way: <https://fdp.org/RESOURCE_TYPE>
        :type resource_type: str
        """
    

    def link_resource(self, graph: Graph, resource_subject: str, parent_purl: URIRef) -> Graph:
        """Add the "resource_subject DCTERMS:isPartOf parent_purl"
          relationship to the resource graph. This relationship is necessary for
          any resource that is uploaded to the FDP.

        :param graph: Graph containing resource description
        :type graph: Graph
        :param resource_subject: subject uri of resource
        :type resource_subject: str
        :param parent_purl: PURL/uri of parent resource
        :type parent_purl: URIRef
        :return: modified resource description
        :rtype: Graph
        """
        # decision: graph interaction, should that be in parse or is it fine in client?

    def upload_resource(self, graph: Graph, resource_subject: str, parent_purl: URIRef, resource_type: str) -> str:
        """Combines link_resource and post_resource to upload a complete resource
        description.

        :param graph: Graph containing resource description
        :type graph: Graph
        :param resource_subject: subject uri of resource
        :type resource_subject: str
        :param parent_purl: PURL/uri of parent resource
        :type parent_purl: URIRef
        :param resource_type: The resource type/class name on the FDP,
        this is case sensitive <https://fdp.org/RESOURCE_TYPE>
        :type resource_type: str
        :return: Location of the new resource on the FDP ie URL
        :rtype: str
        """
    
    def get_resource_children(self, graph: Graph) -> Iterator:
        # graph interaction
        """
        Obtain child nodes of FDP resource.
        
        :param graph: A graph to query
        :type graph: RDFLib Graph
        :return: query result
        :rtype: QueryResult Object
        """

    def get_resource_id(self, graph: Graph, resource_type: URIRef) -> Iterator:
        # graph interaction
        """Obtain all dcterms:identifier objects associated to the
         resource type in the graph.

        :param graph: Graph representation of a resource description
        :type graph: Graph
        :param resource_type: dcat or alternative namespace class that
          the target resource is defined as
        :type resource_type: URIRef
        :yield: query results
        :rtype: Iterator
        """
    
    def remove_subject(self, graph: Graph, subject_uri: URIRef) -> None:
        # Graph interaction necessary to update content of a fdp resource
        # based on remove_blank_node in FDPClient
        """Remove all associated triples to a subject within
        the given graph.

        :param graph: _description_
        :type graph: Graph
        :param subject_uri: _description_
        :type subject_uri: URIRef
        """
    
    def update_resource_graph(self, new_graph: Graph, resource_url: URIRef, resource_type: URIRef):
        # graph interaction and fdp interaction
        """
        Update resource with new content. To ensure PUT requests
        succeeds, we get the current content on the FDP and
        replace all values that are in the graph in the
        graph obtained from the FDP.
        We use the resource_type to extract the resource dcterms:identifier
        as the resource described should be the same.

        :param resource_url: the url of the FDP resource that should be able to handle requests
        :type resource_url: str
        :param resource_type: RDFLib DCAT resource type URIRef
        :type resource_type: RDFLib DCAT resource type URIRef
        :param new_graph: Graph with new content
        :type new_graph: RDFLib Graph
        :return: updated FDP resource rdf graph
        :rtype: RDFLib Graph
        """
    
    def get_dict_of_dataset_ids(self, catalog_graph: Graph) -> dict:
        # graph interaction and fdp interaction
        """Get all dataset URL's and dcterm:identifiers for a given catalog

        :param catalog_graph: a graph containing a FDP catalog resource
        :type catalog_graph: Graph
        :return: dictionary with key=dataset identifier: value=purl
        :rtype: dict
        """
    
    def get_blank_nodes(self, graph: Graph) -> list:
        """Obtain blank node id's inside the graph

        :param graph: Graph representation of resource metadata
        :type graph: Graph
        :return: A list of URIRef's that are a blank node in the graph
        :rtype: list
        """