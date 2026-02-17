from abc import ABCMeta, abstractmethod
from rdflib import Graph, URIRef
from os import getenv

class AbstractClient(metaclass=ABCMeta):

    def __init__(self, config) -> None:
        self.config = config
        
    
    @abstractmethod
    def connection_status(self) -> int:
        """Basic function to check if connection to a FDP is possible

        :return: server response status code
        :rtype: int
        """


    @abstractmethod
    def get_api_token(self, keyring_service: str, keyring_username: str) -> str:
        """        This function generates an bearer-token:
        https://swagger.io/docs/specification/authentication/bearer-authentication/
        This is a token that can be used to authenticate your requests to the FDP server. The password should be aquired through a keyring service.

        :param keyring_service: Service name in keyring system
        :type keyring_service: str
        :param keyring_password: Keyring username for service
        :type keyring_password: str
        :return: An API token
        :rtype: str
        """

    @abstractmethod
    def get_resource(self, url: str) -> str:
        """Get the metadata of a resource from the content of a location
        on the FDP.

        :param url: URL to resource
        :type url: str
        :return: _description_
        :rtype: str
        """
        # decision: always output str or Graph? should both options have a function?
    
    @abstractmethod
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
    
    @abstractmethod
    def publish_resource(self, resource_url: URIRef):
        """Set the status of a resource metadata description to public

        :param resource_url: URL to the target resource
        :type resource_url: URIRef
        """
    
    @abstractmethod
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
    

    def get_dict_of_child_ids(self, resource_graph: Graph) -> dict:
        # graph interaction and fdp interaction
        """Get all child URL's and dcterm:identifiers for a given catalog.
        Relies on get_blank_nodes in GraphInteractor

        :param resource_graph: a graph containing a FDP catalog resource
        :type resource_graph: Graph
        :return: dictionary with key=dataset identifier: value=purl
        :rtype: dict
        """
    