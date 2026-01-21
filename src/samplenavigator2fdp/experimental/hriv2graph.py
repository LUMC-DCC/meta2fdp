from rdflib import Graph, DCTERMS, URIRef, Namespace

class hriv2graph(Graph):
    def __init__(self, store = "default", identifier = None, namespace_manager = None, base = None, bind_namespaces = "rdflib"):
        super().__init__(store, identifier, namespace_manager, base, bind_namespaces):
        self.VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")
        self.graph, self.prefix_map = self.prepared_graph()

    def prepared_graph(self):
        # add VCARD to namespace as the default rdflib namesapce doesn't have it yet:

        graph = Graph(bind_namespaces="rdflib")
        graph.bind("vcard", self.VCARD)
        # reverse namespace prefix mapping so we can parse prefixes used in template
        prefix_map = {}
        for prefix, uri in graph.namespaces():
            prefix_map[prefix.lower()] = uri
        prefix_map["dct"] = DCTERMS # map dct to the DCTERMS namespace, as the RDFLIB uses dcterms as a prefix instead.
        return graph, prefix_map

    def convert_prefix(self, string: str):
        """
        This function converts a string that contains a prefix into
        a uri with appropriate namespace.
        """
        if type(string) == float:
            return "previous"
        prefix, value = string.split(":")
        try:
            uri = self.prefix_map[prefix]
            return URIRef(uri + value)
        except KeyError:
            print(Warning("encountered a : in a non uri: {}".format(string)))
            return 0
        
            

