from abc import ABCMeta
from rdflib import Graph, URIRef

class AbstractExtendedGraph(Graph, metaclass=ABCMeta):
    """An abstract class that edits the content of a rdflib Graph. Functions should
    always output the new graph, as there are cases where the desired outcome
    is that the original graph is maintained while a copy of the graph is edited
    and used for a different goal.
    """
    #decision: we can make this a seperate class that manipulates a Graph object explicitly
    # or we can extend the Graph object with the functionality of this type of class
    # see the Converter class an how it is making a HRI specific class in the init

    def __init__(self) -> None:
        self.graph


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


    def subject_replace(self, graph: Graph, new_subject: URIRef, current_subject: URIRef) -> Graph:
        """Replaces the subject (_s_, p, o) in a given graph.

        :param graph: Graph to replace the main subject from
        :type graph: Graph
        :param new_subject: New subject URI
        :type new_subject: URIRef
        :param current_subject: Original uri of subject
        :type current_subject: URIRef
        :return: Modified graph
        :rtype: Graph
        """
    

    def subject_delete(self, graph: Graph, subject_uri: URIRef) -> Graph:
        # Graph interaction necessary to update content of a fdp resource
        # based on remove_blank_node in FDPClient
        """Remove all associated triples to a subject within
        the given graph.

        :param graph: Graph to delete the main subject from
        :type graph: Graph
        :param subject_uri: subject URI
        :type subject_uri: URIRef
        :return: Modified graph
        :rtype: Graph
        """
    

    def merge_strings(self, graph: Graph, subject_uri: URIRef, predicate: URIRef) -> Graph:
        """Merge multiple strings associated to the same subject predicate pair.
        #HACK implemented for the LLS usecase due to the lack of catalog 
        # resources in the Health-RI health data catalog. As context of a dataset 
        # that was described in the description of the catalog would be missing 
        # if only dataset properties were shown in the Health-RI catalog.

        :param graph: Graph to merge strings in
        :type graph: Graph
        :param subject_uri: subject URI that has a predicate with multiple strings
        :type subject_uri: URIRef
        :param predicate: predicate associated to the collection of strings
        :type predicate: URIRef
        :return: Modified graph
        :rtype: Graph
        """
    

    def get_blank_nodes(self, graph: Graph) -> list[URIRef]:
        """Obtain blank node id's inside the graph

        :param graph: Graph representation of resource metadata
        :type graph: Graph
        :return: A list of URIRef's that are a blank node in the graph
        :rtype: list[URIRef]
        """
    

    def get_resource_id(self, graph: Graph, resource_type: URIRef) -> list[str]:
        # graph interaction
        """Obtain all dcterms:identifier objects associated to the
         resource type in the graph.

        :param graph: Graph representation of a resource description
        :type graph: Graph
        :param resource_type: dcat or alternative namespace class that
          the target resource is defined as
        :type resource_type: URIRef
        :return: A list of strings that identify the resource
        :rtype: list[str]
        """


    def get_resource_children(self, graph: Graph) -> list[URIRef]:
        # graph interaction
        """ Obtain child nodes/resources of FDP resource.
        
        :param graph: A graph to query
        :type graph: RDFLib Graph
        :return: A list of URI's that refer to child nodes/resources
        :rtype: list[URIRef]
        """

    