"""
    Interface to interact FDP content
    source: https://github.com/Orphanet/orphadata-fdp-populator/blob/master/FDPClient.py
"""
import requests
import json



class FDPClient:
    """
    Interface to interact FDP content
    source: https://github.com/Orphanet/orphadata-fdp-populator/blob/master/FDPClient.py
    """

    # The main URL of the FDP server
    FDP_URL = "https://example-fdp.nl"
    # username of an FDP admin
    FDP_ADMIN_USERNAME = "albert.einstein@example.com" 
    # password of an FDP admin
    FDP_ADMIN_PASSWORD = "password" 
    # this is the URL of the parent resource
    FDP_P_URL = "https://example-fdp.nl/catalog/ac5d6134-6b7b-4989-80dd-5b1714023e3d" 

    def __init__(self, fdp_url, username, password, persistent_url):
        self.FDP_URL = fdp_url # this is the main URL of the FDP server
        self.FDP_ADMIN_USERNAME = username
        self.FDP_ADMIN_PASSWORD = password
        self.FDP_P_URL = persistent_url # this is the URL of the parent resource

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
        url = self.FDP_URL + "/tokens"

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
        url = self.FDP_URL + "/" + resource_type
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
        print(response.status_code) #check server response
        #print(response.headers)
        print(response.text)
        #print(response.content)
        resource_url = response.headers["Location"] # get the FDP server URL of the new resource description
        try:
            resource_url = response.headers["Location"]
        except :
            print("Error getting location url")
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
        # print(response.status_code)
        # print(response.headers)
        # print(response.text)

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
        print(response)
        return response
