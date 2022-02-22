import json
import base64
import os
import logging
import logging.handlers
from requests import post, get
from dotenv import load_dotenv

logging.basicConfig(filename='desydoorclient.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)


class DesyDoorClient(object):
    """
    RESTful Web-service authentication client for DESY Door user portal.
    """

    def __init__(self):
        load_dotenv()
        self.__door_rest_root = os.environ["DOOR_REST_ROOT"] or None
        self.__door_rest_token = os.environ["DOOR_REST_TOKEN"] or None
        # Set required door token header for any HTTP call
        self.__door_header_token = {"x-door-token": self.__door_rest_token}

    def login(self, username, password, retry=True, fields=None):
        # First encode the password in base64
        message_bytes = password.encode('ascii')
        base64_bytes = base64.b64encode(message_bytes)
        base64_password = base64_bytes.decode('ascii')
        # Make an HTTP post request with username and encoded password
        r = post(self.__door_rest_root + "/doorauth/auth",
                 data={'user': username, 'pass': base64_password}, headers=self.__door_header_token)
        if r.status_code == 200:
            # status 200 means user authenticated
            logging.info('Username has been succesfully authenticated: %s', username)
            return True, r.json()['userdata']['userid']
        elif r.status_code == 401:
            # status 401 means unauthorized for different reasons: wrong password, wrong token,
            # server not allowed to connect to
            try:
                json_response = json.loads(r.text)
                logging.warning('%s - %s', json_response["message"], username)
            except json.decoder.JSONDecodeError:
                logging.warning("Error decoding JSON response %s", r.status_code)
                logging.warning(r.text)
        elif r.status_code == 404:
            # status 404 means username does not exist
            logging.warning('Username does not exist: %s', username)
        elif r.status_code == 400:
            # status 400 means no valid api call
            logging.error('%s - %s', r.text, r.url)
        return False

    def get_user_roles(self, user_id):
        r = get(self.__door_rest_root + "/roles/userid/" + str(user_id), headers=self.__door_header_token)
        if r.status_code == 200:
            try:
                roles = r.json()['roles']
                return roles
            except KeyError:
                logging.warning('No roles assigned to userid: %s', user_id)
                return False
        else:
            logging.warning('Roles could not be checked for userid: %s', user_id)
        return False

    def get_institute(self, institute_id):
        r = get(self.__door_rest_root + "/institutes/id/" + institute_id, headers=self.__door_header_token)
        if r.status_code == 200:
            return r.json()['institute metadata']

    def get_institute_list(self):
        r = get(self.__door_rest_root + "/institutes/list/", headers=self.__door_header_token)
        if r.status_code == 200:
            return r.json()['institute metadata']
