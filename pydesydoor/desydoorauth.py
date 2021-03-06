import json
import base64
import logging
import logging.handlers
from requests import post, get
from pydesydoor.desydoorapi import DesyDoorAPI


class DesyDoorAuth(DesyDoorAPI):
    """
    RESTful Web-service user authentication client for DESY Door user portal.
    """

    def get_door_request(self, url):
        r = get(url, headers=self.get_door_header_token(), verify=False)
        r.raise_for_status()
        return r

    def post_door_request(self, url):
        r = post(url, headers=self.get_door_header_token(), verify=False)
        r.raise_for_status()
        return r

    def login(self, username, password, retry=True, fields=None):
        # First encode the password in base64
        message_bytes = password.encode('ascii')
        base64_bytes = base64.b64encode(message_bytes)
        base64_password = base64_bytes.decode('ascii')
        # Make an HTTP post request with username and encoded password
        r = post(self.get_door_rest_root() + "/doorauth/auth",
                 data={'user': username, 'pass': base64_password}, headers=self.get_door_header_token(), verify=False)
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
