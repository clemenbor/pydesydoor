import json
from datetime import datetime
from pydesydoor.desydoorapi import DesyDoorAPI


class DoorPyISPyB(DesyDoorAPI):
    """
    RESTful Web-service API client to generate the data format required to import
    data into py-ISPyB.
    """
    def get_full_proposal_to_pyispyb(self, door_proposal_id, with_leader=True, with_cowriters=True, with_sessions=True,
                                     with_session_participants=True):
        """
           Get the full proposal data (sessions, etc) from DOOR in format for py-ispyb

           :param str door_proposal_id: The DOOR proposal id
           :param boolean with_leader: True/False depending if the proposal leader data is needed
           :param boolean with_cowriters: True/False depending if the proposal cowriters data is needed
           :param boolean with_sessions: True/False depending if the proposal sessions data is needed
           :param boolean with_session_participants: True/False depending if the session participants data is needed
        """
        ispyb_proposal = {}
        # Getting the proposal data without leader and cowriters
        proposal_data = self.get_proposal_to_pyispyb(door_proposal_id, with_leader, with_cowriters)
        ispyb_proposal["proposal"] = proposal_data
        if with_sessions:
            sessions_data = self.get_sessions_to_pyispyb(door_proposal_id, with_session_participants)
            ispyb_proposal["sessions"] = sessions_data
        return json.dumps(ispyb_proposal, indent=4, sort_keys=True, default=str)

    def get_proposal_to_pyispyb(self, door_proposal_id, with_leader=True, with_cowriters=True):
        """
           Get the proposal data from DOOR in format for py-ispyb

           :param str door_proposal_id: The DOOR proposal id
           :param boolean with_leader: True/False depending if the leader data is needed
           :param boolean with_cowriters: True/False depending if the cowriters data is needed
        """
        data = {}
        door_proposal = self.get_proposal(door_proposal_id)
        data["title"] = door_proposal["title"]
        data["proposalNumber"] = str(door_proposal["proposalNumber"])
        data["proposalCode"] = door_proposal["proposalCode"]
        data["proposalType"] = "MX"
        data["bltimeStamp"] = None
        data["state"] = "Open"
        persons = []
        # Set the PI
        if door_proposal["proposalPI"]:
            # First one in the list will be the PI
            pi = self.get_user_to_pyispyb(door_proposal["proposalPI"])
            persons.append(pi)
        if with_leader:
            # Set the Leader
            if door_proposal["proposalLeader"]:
                leader = self.get_user_to_pyispyb(door_proposal["proposalLeader"])
                persons.append(leader)
        if with_cowriters:
            # Set the co-writers
            if door_proposal["proposalCowriters"]:
                if not isinstance(door_proposal["proposalCowriters"], int):
                    # There is more than one co-writer
                    cowriter_ids = self.split_multiple_by_comma(door_proposal["proposalCowriters"])
                    for cowriter_id in cowriter_ids:
                        cowriter = self.get_user_to_pyispyb(cowriter_id)
                        cowriter["type"] = "cowriter"
                        persons.append(cowriter)
                else:
                    # There is only one co-writer
                    cowriter = self.get_user_to_pyispyb(door_proposal["proposalCowriters"])
                    persons.append(cowriter)
        # Add proposal persons
        data["persons"] = persons
        # Add proposal data
        return data

    def get_user_to_pyispyb(self, door_user_id, with_laboratory=True):
        """
           Get the user data from DOOR in format for py-ispyb

           :param str door_user_id: The DOOR user id
           :param boolean with_laboratory: True/False depending if the Laboratory/Institute data is needed
        """
        user = {}
        door_user = self.get_user(door_user_id)
        user["givenName"] = door_user["givenName"]
        user["familyName"] = door_user["familyName"]
        user["emailAddress"] = door_user["emailAddress"]
        user["login"] = door_user["login"]
        if with_laboratory:
            user["laboratory"] = self.get_laboratory_to_pyispyb(door_user["laboratoryId"])
        user["phoneNumber"] = str(door_user["phoneNumber"])
        user["siteId"] = int(door_user_id)
        return user

    def get_laboratory_to_pyispyb(self, laboratory_id):
        door_laboratory = self.get_institute(laboratory_id)
        return door_laboratory

    def get_sessions_to_pyispyb(self, door_proposal_id, with_persons=True):
        """
           Get the proposal sessions data from DOOR in format for py-ispyb

           :param str door_proposal_id: The DOOR proposal id
           :param boolean with_persons: True/False depending if the session participants data is needed
        """
        sessions = []
        door_sessions = self.get_proposal_sessions(door_proposal_id)
        if door_sessions:
            add_session = dict()
            for session in door_sessions:
                add_session["expSessionPk"] = int(session)
                datetime_start = datetime.strptime(door_sessions[session]["startDate"], '%Y-%m-%d %H:%M:%S')
                add_session["startDate"] = datetime_start.isoformat()
                datetime_end = datetime.strptime(door_sessions[session]["endDate"], '%Y-%m-%d %H:%M:%S')
                add_session["endDate"] = datetime_end.isoformat()
                add_session["beamlineName"] = door_sessions[session]["beamlineName"]
                add_session["scheduled"] = door_sessions[session]["scheduled"]
                add_session["nbShifts"] = door_sessions[session]["nbShifts"]

                if door_sessions[session]["beamlineOperator"]:
                    operator = self.get_user_to_pyispyb(door_sessions[session]["beamlineOperator"], False)
                    add_session["beamlineOperator"] = " ".join([operator["givenName"], operator["familyName"]])
                if with_persons:
                    persons = []
                    remotes = self.get_participants(door_sessions[session]["participants"], "remote")
                    if remotes:
                        persons += remotes
                    on_sites = self.get_participants(door_sessions[session]["participants"], "on-site")
                    if on_sites:
                        persons += on_sites
                    data_onlys = self.get_participants(door_sessions[session]["participants"], "data-only")
                    if data_onlys:
                        persons += data_onlys
                    # Add session participants
                    add_session["persons"] = persons
                sessions.append(add_session)
        return sessions

    def get_participants(self, participants, participant_type):
        """
           Helper function to setup the session participants data
        """
        users = []
        array_participants = None
        if participants[participant_type]:
            array_participants = self.split_multiple_by_comma(str(participants[participant_type]))
        if array_participants:
            for participant in array_participants:
                if participant:
                    participant = self.get_user_to_pyispyb(participant, True)
                    # By now we consider only the remote option
                    # the remote field in ISPyB Session_has_Person table is a tinyint
                    # Door apparently is not storing the participant session role (Staff, Principal Investigator, etc)
                    if participant_type == "remote":
                        session_options = dict()
                        session_options["remote"] = 1
                        participant["session_options"] = session_options
                    users.append(participant)
            return users
