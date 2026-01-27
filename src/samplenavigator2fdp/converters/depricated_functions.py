
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