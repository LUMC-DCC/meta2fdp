from samplenavigator2fdp.graphutils.graphutils import convert_prefix, prepared_graph

graph, prefix_map = prepared_graph()
with open("schema/shacl/v2/Dataset.ttl", "r") as file:
    graph.parse(file)


def _prep_uris(URIs):
    uri_list = ""
    for uri in URIs:
        uri_list = uri_list + "<" + uri + ">\n"
    return uri_list

def _match_uris(URIs):
    """
    Finds the class that overlaps the most with the given list of URI's
    """
    request_body = _prep_uris(URIs)
    query = """PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?targetClass (COUNT(?targetClass) AS ?count)
WHERE { ?shape a sh:NodeShape ;
        sh:targetClass ?targetClass ;
        sh:property ?property .
?property sh:path ?predicate
VALUES ?predicate {""" + request_body + """
 }
 }
GROUP BY ?targetClass
"""
    qres = graph.query(query)
    ranked_classes = NotImplemented
    results = []
    for result in qres:
        results.append(result)
    results.sort()
    return ranked_classes

URIs = ["http://purl.org/dc/terms/description","http://purl.org/dc/terms/type"]
_match_uris(URIs)




def extract_creator(graph: Graph, node):
    creator_query= """
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

CONSTRUCT { 
  <https://fdp.example.org/new> dcterms:creator ?c . 
  ?c a foaf:Agent . 
  ?c dcterms:identifier ?identifier . 
  ?c foaf:homepage ?homepage . 
  ?c foaf:mbox ?mbox . 
  ?c foaf:name ?name 
}
WHERE { 
  ?c dcterms:identifier ?identifier; 
     foaf:homepage ?homepage; 
     foaf:mbox ?mbox; 
     foaf:name ?name .
  FILTER(STR(?c) = \"""" + str(node) + """\")
}

"""
    resource_creator = graph.query(creator_query)
    return resource_creator.graph

#TODO remove "    dcterms:creator " from first line and replace with "    "
#TODO replace ".\n" with ",\n" to end of creator string
#TODO add it back to the first creator and replace ",\n" with "\n\n" at the end of merged string
#TODO remove all creators from graph
#TODO remove last \n\n from target graph
#TODO append target graph ttl with reordered creators

def cleanup_creator(string: str):
    """
    clean up string so it follows the ttl pattern for multiple blank nodes
    associated to a single class property
    """
    string = string.lstrip("    dcterms:creator ")
    string = "    " + string
    string = string.rstrip(".\n")
    clean_string = string + ",\n"
    return clean_string


def extract_creator_ttl(graph: Graph, node):
    """
    Serialize a single creator and extract the ttl
    Then add a tab infront of every line (four spaces)
    """
    creator_graph = extract_creator(graph, node)
    graph_string = creator_graph.serialize()
    print(graph_string)
    creator_ttl = graph_string.split("\n\n")[1]

    return creator_ttl


def prep_creator_inject(string: str):
    """
    set up collection of creators to be appended
    to the serialized target graph
    """
    string = string.lstrip("    ")
    string = "    dcterms:creator " + string
    string = string.rstrip(",\n")
    prepped_string = string + ".\n\n"
    return prepped_string


def inject_ordered_creators(source_graph: Graph, nodes: list, target_graph: Graph):
    """
    From the source graph extract the creators in the order of appearance
    and inject them at the end of the resource description.
    """
    ttl_extension = ""
    for node in nodes:
        creator_ttl = extract_creator_ttl(source_graph, node)
        creator_ttl = cleanup_creator(creator_ttl)
        ttl_extension = ttl_extension + creator_ttl
        target_graph.remove((node, None, None)) # now not used!!!!
    ttl_extension = prep_creator_inject(ttl_extension)
    target_string = target_graph.serialize()
    target_string = target_string.rstrip("\n\n")
    target_string = target_string + ttl_extension
    return target_string