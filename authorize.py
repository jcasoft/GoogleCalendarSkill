# From your command line go to folder skill
#
# cd /opt/mycroft/skills
#
# python GoogleCalendarSkill --noauth_local_webserver
# 
# checking for cached credentials
#
# Go to the following link in your browser on computer with browser (this link may be different on each computer):
# 
# Enter verification code: 4/oxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx   (Please copy the code generated, and paste it there)
#

import httplib2
import os

from googleapiclient import discovery
from googleapiclient import errors
import oauth2client
from oauth2client import file
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow

from json import JSONEncoder

import json
import time
from collections import OrderedDict
from HTMLParser import HTMLParser
import datetime

__author__ = 'jcasoft'

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


SCOPES = 'https://www.googleapis.com/auth/calendar'
CID = "992603803855-06urqkqae0trrr2dfte4vljmj8ts2om2.apps.googleusercontent.com"
CIS = "y6K5-YmVEcN9riOTnAVeMYvc"
APPLICATION_NAME = 'Mycroft Google Calendar Skill'


def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    print("checking for cached credentials")
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,'mycroft-googlecalendar-skill.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        credentials = tools.run_flow(OAuth2WebServerFlow(client_id=CID,client_secret=CIS,scope=SCOPES,user_agent=APPLICATION_NAME),store)
        print 'Storing credentials to ' + credential_dir
	print 'Your Google Calendar Skill is now authenticated '
    else:
	print 'Loaded credentials for Google Calendar Skill from ' + credential_dir
    return credentials

def config_file():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.mycroft')
    filename = os.path.join(credential_dir,'mycroft.conf')
    if os.path.isfile(filename):
        try:
            with open(filename, "r") as jsonFile:
                data = json.load(jsonFile, object_pairs_hook=OrderedDict)
                resultado = list(v for k,v in data.items() if "GoogleCalendarSkill" in k.lower())
                if len(resultado) == 0:	
		    print "Updating configuration file"
                    data["GoogleCalendarSkill"]={"loginEnabled":False,"loginLevel":4,"calendar_id": "YOUR_GMAIL@gmail.com", \
                                                "maxResults": 10,"gmt": "-06:00","timeZone": "America/El_Salvador", \
                                                "attendees_own":"YOUR_GMAIL@gmail.com","attendees_family":"MY_WIFE@gmail", \
                                                "attendees_work":"MY_SALES_TEAM@gmail.com","reminders_email": 1440, \
                                                "reminders_popup": 10,"default_duration": 2,"time_format": 12}
                    try:
                        with open(filename, "w") as jsonFile:
                            jsonFile.write(json.dumps(OrderedDict(data), indent=4, sort_keys=False))
                    except IOError as error:
                            print "Saving configuration file failed"
                            return False
                    time.sleep(10)
                else:
                    return data

        except IOError as error:
            print "Reading config file failed"
            return False
    else:
        print "Creating new Config file"
        data["GoogleCalendarSkill"]={"loginEnabled":False,"loginLevel":4,"calendar_id": "YOUR_GMAIL@gmail.com", \
                                    "maxResults": 10,"gmt": "-06:00","timeZone": "America/El_Salvador", \
                                    "attendees_own":"YOUR_GMAIL@gmail.com","attendees_family":"MY_WIFE@gmail", \
                                    "attendees_work":"MY_SALES_TEAM@gmail.com","reminders_email": 1440, \
                                    "reminders_popup": 10,"default_duration": 2,"time_format": 12}
        try:
            with open(filename, "w") as jsonFile:
                jsonFile.write(json.dumps(OrderedDict(data), indent=4, sort_keys=False))
        except IOError as error:
            print "Saving configuration file failed: "
            return False

        time.sleep(10)


config_file()
credentials = get_credentials()
http = credentials.authorize(httplib2.Http())
global service
service = discovery.build('calendar', 'v3', http=http)

now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
eventsResult = service.events().list(calendarId='primary', timeMin=now, maxResults=10, singleEvents=True, orderBy='startTime').execute()
events = eventsResult.get('items', [])

if not events:
    print('No upcoming events found.')
for event in events:
    start = event['start'].get('dateTime', event['start'].get('date'))

    start = start[:22]+start[(22+1):]

    if '+' in start:
	start = datetime.datetime.strptime(start,"%Y-%m-%dT%H:%M:%S+%f")
    else:
	start = datetime.datetime.strptime(start,"%Y-%m-%dT%H:%M:%S-%f")

    startHour = ("{:d}:{:02d}".format(start.hour, start.minute))
    startHour = time.strptime(startHour,"%H:%M")
    startHour = time.strftime("%I:%M %p",startHour)
    if (startHour[0]=='0'): startHour = startHour.replace('0','',1)

    print('-->'+ event['summary'] + ' at ' + startHour)


print 'Your Google Calendar Skill is now authenticated '
