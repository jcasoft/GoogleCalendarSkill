#from __future__ import print_function
import httplib2
import os

from googleapiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools
from oauth2client import file
from oauth2client.client import OAuth2WebServerFlow

import calendar
import datetime
import time
import sys

import json
from json import JSONEncoder

event_json = ""
if len(sys.argv) > 1: 
	event_json = json.loads(sys.argv[1])

__author__ = 'jcasoft'

SCOPES = 'https://www.googleapis.com/auth/calendar'
CID = "992603803855-06urqkqae0trrr2dfte4vljmj8ts2om2.apps.googleusercontent.com"
CIS = "y6K5-YmVEcN9riOTnAVeMYvc"
APPLICATION_NAME = 'Mycroft Google Calendar Skill'

def get_credentials():

    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,'mycroft-googlecalendar-skill.json')
    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()

    if not credentials or credentials.invalid:
        credentials = tools.run_flow(OAuth2WebServerFlow(client_id=CID,client_secret=CIS,scope=SCOPES,user_agent=APPLICATION_NAME),store)

    return credentials


def main():
	credentials = get_credentials()
	http = credentials.authorize(httplib2.Http())
	service = discovery.build('calendar', 'v3', http=http)

	event = service.events().insert(calendarId='primary', body=event_json).execute()

	status = event.get('status')
    	htmlLink = event.get('htmlLink')

    	if status == 'confirmed' and len(htmlLink) > 43:
		print ('confirmed')
    	else:
		print ('error')

if __name__ == '__main__':
    main()