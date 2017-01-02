# From your command line: 
#
# python mycroft-googlecalendar-skill --noauth_local_webserver
# 
# checking for cached credentials
#
# Go to the following link in your browser on computer with browser (this link may be different on each computer):
# 
# https://accounts.google.com/o/oauth2/v2/auth?scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar&redirect_uri=urn%3Aietf%3Awg%3Aoauth%3A2.0%3Aoob&response_type=code&client_id=992603803855-06urqkqae0trrr2dfte4vljmj8ts2om2.apps.googleusercontent.com&access_type=offline
#
# Enter verification code: 4/oxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx   (Please copy the code generated, and paste it there)
#

import sys
import os
import datetime
import time
path = os.path.dirname(sys.modules[__name__].__file__)
path = os.path.join(path, '..')
sys.path.insert(0, path)

import httplib2
import os
from googleapiclient import discovery
import oauth2client
from oauth2client import file
from oauth2client import client
from oauth2client import tools
from oauth2client.client import OAuth2WebServerFlow


"""Handles basic authentication and provides feedback in form of upcoming
   events (if any) after completion.
"""

SCOPES = 'https://www.googleapis.com/auth/calendar'
CID = "992603803855-06urqkqae0trrr2dfte4vljmj8ts2om2.apps.googleusercontent.com"
CIS = "y6K5-YmVEcN9riOTnAVeMYvc"
APPLICATION_NAME = 'Mycroft Google Calendar Skill'

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """

    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    print "checking for cached credentials"
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


credentials = get_credentials()
http = credentials.authorize(httplib2.Http())
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
