from rdflib import Graph, RDFS
#from pyschacl import validate
import yaml
import os
from pandas import DataFrame

class ClassExtractor(object):
    """
    This class extracts all classes from a given SHACL file
    Assumptions:  
    * Any shape that defines a class as a resource should be treated as a main component
    of a FAIR Data Point.
    * Any dataframe/table that is being classified is describing a single class in the SHACL
    """
    def __init__(self, config_path="config/FDP/configuration.yaml"):
        self.SHACL_path = self.get_SHACL_path(config_path)
        self.graph = Graph()
        self.parse_shacl_folder(self.SHACL_path)
    
    def get_SHACL_path(self, config_path):
        """
        Get path to folder with SHACL files or assign default value.

        :param config_path: path to config file
        :type config_path: String
        :return: Path to SHACL files to comply to
        :rtype: String
        """ 
        with open(config_path, "r") as config_file:
            config = yaml.safe_load(config_file)
        try:
            path = config["file_paths"]["schacl_directory"]
        except KeyError:
            path = "schema/shacl/v2"
        return path
    
    def parse_shacl(self, path): #TODO preped graph
        """
        Add the given SHACl to the graph
        """
        with open(path) as file:
            self.graph.parse(file)

    def parse_shacl_folder(self, path):
        shacl_files = os.listdir(path)
        for file_path in shacl_files:
            self.parse_shacl(path + "/" + file_path)
    
    ##################################
    # class detection in data
    ##################################

    def _detect_uri(self, column):
        URIs = []
        for cell in column:
            if ":" in cell:
                full_uri = convert_prefix(cell)
                if type(full_uri) == int:
                    continue
                else:
                    URIs.append(full_uri)
            elif "https:" in cell or "http:" in cell:
                URIs.append(cell)
            elif cell == "":
                continue
            else:
                continue
        return URIs

    
    def _find_uri_column(self, table: DataFrame):
        """        .
        This function tries to detect the column that contains the 
        URIs defining the values for a particular class associated to
        the table.
        """
        RDFS_terms = set([RDFS.Literal, RDFS.Resource])
        columns = table.columns
        for col in columns:
            URIs = self._detect_uri(table.loc[:, col])
            matching = set(URIs) & set(RDFS_terms)
            if len(URIs) > 0 and len(matching) == 0:
                return col, URIs
        raise(Exception(add_note="could not find any clean column of property URIs. Are you using rdfs:Literal or rdfs:Resource as a property definition instead of valuetype?"))
    

    def _uri_valuetype(self, uri):
        """
        We try to resolve the URI on the web to see if we can figure out
        the value/subject type allowed for the given predicate.
        """
        value_type = NotImplemented
        return value_type
    

    def _detect_value_column(self, uri_column, table):
        value_column = NotImplemented
        return value_column
    

    def _prep_uris(self, URIs):
        uri_list = ""
        for uri in URIs:
            uri_list = uri_list + "<" + str(uri) + ">\n"
        return uri_list

        
    def _match_uris(self, URIs):
        """
        Finds the class that overlaps the most with the given list of URI's
        """
        request_body = self._prep_uris(URIs)
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
        qres = self.graph.query(query)
        results = []
        for result in qres:
            results.append(result)
        results.sort()
        ranked_classes = results.copy()
        return ranked_classes


    def detect_class(self, table):
        """
        We work on the assumption that in no matter the shape of the
        provided data. There will be two columns that contain
        the information required for populating an RDF formatted file.
        These columns are: The URI to defining the value, and the value itself
        """
        uri_column, URIs = self._find_uri_column(table)
        print(uri_column)
        object_class_scores = self._match_uris(URIs)
        return object_class_scores
    

    # ###########################################
    # # generate RDF !!! not relevant for current class !!!
    # ############################################

    # def auto_generate_rdf(self, table):
    #     """
    #     This function takes a given dataframe and transforms it to an RDF
    #     class based on the most overlapping mandatory properties.
    #     This 
    #     """
    #     graph = prepared_graph()
    #     class_scores = self.detect_class(table)
    #     class_type = class_scores.reverse().pop()
    #     return graph 
    
    # def validate_rdf(self, graph):
    #     """
    #     Validate a given RDF graph and return the report.
    #     """
    #     validation_report = None
    #     return validation_report
    

    