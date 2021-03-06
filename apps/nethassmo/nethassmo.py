import appdaemon.plugins.hass.hassapi as hass
import requests
import time
from configparser import ConfigParser, ExtendedInterpolation
import os
import os.path
import datetime
 
class Nethassmo(hass.Hass):
 
    def initialize(self):
        # READING CONFIG FILE
        self.path = os.path.dirname(os.path.abspath(__file__))
        self.cfg_file = self.path + "/nethassmo.cfg"
        self.config = ConfigParser(delimiters=(':', '='))
        self.config.read(self.cfg_file)
      
        self.data_error = False

        # CHECKING ACCESS DATA IN CONFIG FILE
        if "user" not in self.args:
            self.error("You must enter your Netatmo Username.")
            self.data_error = True
        else:
            self.log("Reading username... OK")
            self.user = self.args['user']

        if "pswd" not in self.args:
            self.error("You must enter your Netatmo Password.")
            self.data_error = True
        else:
            self.log("Reading password... OK")
            self.pswd = self.args['pswd']

        if "client" not in self.args:
            self.error("You must enter your Netatmo Client ID.")
            self.data_error = True
        else:
            self.log("Reading Client ID... OK")
            self.client = self.args['client']

        if "secret" not in self.args:
            self.error("You must enter your Netatmo Client Secret.")
            self.data_error = True
        else:
            self.log("Reading Client Secret... OK")
            self.secret = self.args['secret']
            
        if self.data_error == True:
            self.error("Please provide your Netatmo credential.", level = "ERROR")
        else:
            self.log("Netatmo Access Data: OK")
            self.get_token()
        
        # CHECKING IF OPTION PERSON IS PRESENT AND PERSONS SENSOR ARE SPECIFIED 
        if "persons" in self.args:
            self.persons = self.args['persons']
            if self.persons == []:
                self.error("Add persons' entity to monitor in file apps.yaml", level = "ERROR")
            else:
                for person in self.persons:
                    self.listen_state(self.set_state, entity=person)
        
        # CHECKING IF OPTION GUEST MODE IS PRESENT AND ENTITY IS SPECIFIED
        if "guest_mode_switch" in self.args:
            guest_mode = self.args['guest_mode_switch']
            self.listen_state(self.guestmode, guest_mode)


        now = datetime.datetime.now()
        delta = datetime.timedelta(seconds=30)
        wait = now + delta
        self.run_every(self.refresh_token, wait, 150*60)
        
    
    #################################################
    
    #           get_token FUNCIONN 

    #################################################

    def get_token(self):
        self.config = ConfigParser(delimiters=(':', '='))
        self.config.read(self.cfg_file)
        if not self.config.has_option('TOKEN', 'token'): # REQUSTING TOKEN IF NOT ALREADY PRESENT
            payload = {'grant_type': 'password',
                    'username': self.user,
                    'password': self.pswd,
                    'client_id': self.client,
                    'client_secret': self.secret,
                    'scope': 'read_camera write_camera access_camera'}
            self.log("Requesting Token...")
            try:
                response = requests.post("https://api.netatmo.com/oauth2/token",
                                        data=payload)
                response.raise_for_status()
                access_token = response.json()["access_token"]
                refresh_token = response.json()["refresh_token"]            
                # scope = response.json()["scope"]
                # validity = response.json()["expires_in"]

                self.log("Token acquired. Writing to configuration file...")
                self.config['TOKEN'] = {}
                self.config['TOKEN']['token'] = access_token
                self.config['TOKEN']['refresh'] = refresh_token
                
                
                with open(self.cfg_file, 'w') as configfile:
                    self.config.write(configfile)

            except requests.exceptions.HTTPError as error:
                self.log(error.response.status_code, error.response.text)
        else:
            self.log("Access Token found.")

        self.get_home_data()


    #################################################
    
    #           get_home_data FUNCIONN 

    #################################################

    def get_home_data(self, *args):
        self.config = ConfigParser(allow_no_value=True, delimiters=(':', '='))
        self.config.read(self.cfg_file)
        
        if not self.config.has_section('HOME'): # REQUSTING HOME DATA IF NOT ALREADY PRESENT
            self.log("Requesting Home data...")
            token = self.config['TOKEN']['token']
            params = {
                'access_token': token,
            }

            try:
                response = requests.post("https://api.netatmo.com/api/gethomedata?size=0",
                                        params=params)
                response.raise_for_status()
                self.config['HOME'] = {}
                self.config['PERSONS'] = {}
                
                home_id = response.json()["body"]['homes'][0]['id']
                self.config['HOME']['home_id'] = home_id
                # self.log("Home ID: {}".format(home_id))
                persons = response.json()["body"]['homes'][0]['persons']
                for person in persons:
                    if "pseudo" in person:
                        self.config['PERSONS'][person['pseudo']] = person['id']
                
                with open(self.cfg_file, 'w') as configfile:
                    self.config.write(configfile)
                
            except requests.exceptions.HTTPError as error:
                self.log(error.response.status_code, error.response.text)
        else:
            self.log("Home data found.")

        self.sensors = self.args['persons']
        if self.sensors == []:
            self.error("Add persons' entity to monitor in file apps.yaml", level = "ERROR")
        else:
            if not self.config.has_section('SENSORS'):
                self.log("Adding person sensors to configuration file...")
                self.config['SENSORS'] = {}
                self.config.optionxform=str
                self.config.set('SENSORS', '; Edit value (if needed) with the correspondig name from [PERSONS] section')
                self.config.set('SENSORS', '; e.g. ${PERSONS:name}')
                
                for sensor in self.sensors:
                    friendly_name = self.get_state(sensor, attribute='friendly_name')
                    self.config['SENSORS']['sensor_' + friendly_name.lower()] = '${PERSONS:' + friendly_name.lower() + '}'

                with open(self.cfg_file, 'w') as configfile:
                        self.config.write(configfile)


    #################################################
    
    #           refresh_token FUNCIONN 

    #################################################

    def refresh_token(self, *args):
        self.config = ConfigParser(delimiters=(':', '='))
        self.config.read(self.cfg_file)

        if self.config.has_option('TOKEN', 'refresh'):
            self.log("Refreshing Token validity...")
            client_id = self.client
            client_secret = self.secret
            token = self.config['TOKEN']['token']
            refresh = self.config['TOKEN']['refresh']

            payload = {'grant_type': 'refresh_token',
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'refresh_token': refresh}

            try:
                response = requests.post("https://api.netatmo.com/oauth2/token",
                                        data=payload)
                response.raise_for_status()
                access_token = response.json()["access_token"]
                refresh_token = response.json()["refresh_token"]
                scope = response.json()["scope"]
                if ("write_camera" and "access_camera") not in scope:
                    self.error("Needed scopes are missing. Requesting new token and scope...", level = "WARNING")
                    self.get_token()
                else:
                    if access_token == token:
                        self.log("Token validity refreshed!")
                    else:
                        self.log("Token renewd!")
                        self.config['TOKEN']['token'] = access_token
                        self.config['TOKEN']['refresh'] = refresh_token
                    with open(self.cfg_file, 'w') as configfile:
                        self.config.write(configfile)

            except requests.exceptions.HTTPError as error:
                self.log(error.response.status_code, error.response.text)


    #################################################
    
    #           set_state FUNCIONN 

    #################################################

    def set_state(self, entity, attributes, old, new, kwargs):
        self.config = ConfigParser(delimiters=(':', '='), interpolation=ExtendedInterpolation())
        self.config.read(self.cfg_file)
        token = self.config['TOKEN']['token']
        home = self.config['HOME']['home_id']

        if (new == 'home' and old != new):
            friendly_name = self.get_state(entity, attribute='friendly_name')
            person_id = self.config['SENSORS']['sensor_' + friendly_name.lower()]

            params = {
                'access_token': token,
                'home_id': home,
                'person_ids': '[ "' + person_id + '" ]'
            }
            try:
                response = requests.post("https://api.netatmo.com/api/setpersonshome",
                                        params=params)
                response.raise_for_status()
                status = response.json()["status"]
                self.log("Setting {} home...".format(friendly_name.capitalize()))
                self.log("Response: {}".format(status.upper()))
            except requests.exceptions.HTTPError as error:
                self.log(error.response.status_code, error.response.text)

        elif (new == 'not_home' and old == 'home'):
            friendly_name = self.get_state(entity, attribute='friendly_name')
            person_id = self.config['SENSORS']['sensor_' + friendly_name.lower()]
            
            params = {
                'access_token': token,
                'home_id': home,
                'person_id': person_id
            }
            try:
                response = requests.post("https://api.netatmo.com/api/setpersonsaway",
                                        params=params)
                response.raise_for_status()
                status = response.json()["status"]
                self.log("Setting {} away...".format(friendly_name.capitalize()))
                self.log("Response: {}".format(status.upper()))
            except requests.exceptions.HTTPError as error:
                self.log(error.response.status_code, error.response.text)


    #################################################
    
    #           guestmode FUNCIONN 

    #################################################

    def guestmode(self, entity, attributes, old, new, kwargs):
        self.config = ConfigParser(delimiters=(':', '='))
        self.config.read(self.cfg_file)

        token = self.config['TOKEN']['token']

        params = {
            'access_token': token
        }

        try:
            response = requests.post("https://api.netatmo.com/api/gethomedata?size=0",
                                    params=params)
            response.raise_for_status()
            cameras = response.json()["body"]['homes'][0]['cameras']
            for camera in cameras:
                if (new == 'off'):
                    if (camera['status'] == 'off'):
                        self.log("Turning ON monitoring. This make take few seconds...")
                        try:
                            response = requests.post(camera['vpn_url'] + "/command/changestatus?status=on")
                            response.raise_for_status()
                            status = response.json()["status"]
                            self.log("Response: {}".format(status.upper()))
                        except requests.exceptions.HTTPError as error:
                            self.log(error.response.status_code, error.response.text)
                    else:
                        self.log("Camera is already ON")
                elif (new == 'on'):
                    if (camera['status'] == 'on'):
                        self.log("Turning OFF monitoring. This make take few seconds...")
                        try:
                            response = requests.post(camera['vpn_url'] + "/command/changestatus?status=off")
                            response.raise_for_status()
                            status = response.json()["status"]
                            self.log("Response: {}".format(status.upper()))
                        except requests.exceptions.HTTPError as error:
                            self.log(error.response.status_code, error.response.text)
                    else:
                        self.log("Camera is already OFF")
        
        except requests.exceptions.HTTPError as error:
            self.log(error.response.status_code, error.response.text)

 