from adapt.intent import IntentBuilder
from mycroft.messagebus.message import Message

from mycroft.skills.core import MycroftSkill
from mycroft.configuration import ConfigurationManager
from mycroft.util.log import getLogger
from mycroft.util import record, play_mp3


import httplib2
import os
from googleapiclient import discovery
import oauth2client
from oauth2client import file
from oauth2client import client
from oauth2client import tools
from oauth2client.client import OAuth2WebServerFlow

import calendar
import datetime
import time
from os.path import dirname, abspath, join, expanduser
import sys

import json
from json import JSONEncoder
import subprocess
from tzlocal import get_localzone
from astral import Astral

import dateutil.parser

logger = getLogger(dirname(__name__))
sys.path.append(abspath(dirname(__file__)))

__author__ = 'jcasoft'

SCOPES = 'https://www.googleapis.com/auth/calendar'
CID = "992603803855-06urqkqae0trrr2dfte4vljmj8ts2om2.apps.googleusercontent.com"
CIS = "y6K5-YmVEcN9riOTnAVeMYvc"
APPLICATION_NAME = 'Mycroft Google Calendar Skill by ' + __author__.upper()

loginEnabled = ""
event_json = {}
gmt = "+00:00"
timeZone = ""
email_minutes = 1440
pop_up_minutes = 10
event_duration = 2	# Default duration un hours, if not defined on mycroft.conf
descAgent = ""

"""
****************************************************
Check the location of the Mycroft third_party Skill
****************************************************
"""
python_out 		=  "/usr/bin/python2.7"
third_party_skill	= dir_path = os.path.dirname(os.path.realpath(__file__))
effects 		= third_party_skill + "/effects/"


attendees_own_Email=[]
attendees_family_Email=[]
attendees_work_Email=[]

word_found = ""

def get_credentials():
    """Gets valid user credentials from storage.
    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    global descAgent
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    print "checking for cached credentials"
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)

    credential_path = os.path.join(credential_dir,'mycroft-googlecalendar-skill.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    descAgent = ""
    if not credentials or credentials.invalid:
        credentials = tools.run_flow(OAuth2WebServerFlow(client_id=CID,client_secret=CIS,scope=SCOPES,user_agent=APPLICATION_NAME),store)
    else:
        logger.info('Loaded credentials from ~ .credentials')

    with open(credential_path) as credential_file:
	data = json.load(credential_file)
    descAgent = data['user_agent']

    return credentials



def loggedIn():
    """
    Future implementation
    To do:
	- Verify FaceLogin Skill
	- Verify ProximityLogin Skill (For use with SmartPhone Mycroft Client App and iBeacon function on Rpi)
	- Verify PhoneClientLogin Skill (For use with SmartPhone Mycroft Client App with fingerprint or Unlock code )
	- Maybe VoiceLogin Skill
    """
    return True

def todayDateEnd():
    todayEnd = datetime.datetime.utcnow().replace(hour=23, minute=59, second=59)
    todayEnd += datetime.timedelta(days=1)	# Add extrea dat to rango for GTM deltaset new event at 8:30 am
    todayEnd = todayEnd.isoformat() + 'Z'
    return todayEnd

def tomorrowDateStart():
    tomorrowStart = datetime.datetime.utcnow().replace(hour=00, minute=00, second=01)
    tomorrowStart += datetime.timedelta(days=1)
    tomorrowStart = tomorrowStart.isoformat() + 'Z'
    return tomorrowStart

def tomorrowDateEnd():
    tomorrowEnd = datetime.datetime.utcnow().replace(hour=23, minute=59, second=59)
    tomorrowEnd += datetime.timedelta(days=2)	# Add extrea dat to rango for GTM delta
    tomorrowEnd = tomorrowEnd.isoformat() + 'Z'
    return tomorrowEnd

def otherDateStart(until):
    otherDayStart = datetime.datetime.utcnow().replace(hour=00, minute=00, second=01)
    otherDayStart += datetime.timedelta(days=until)
    otherDayStart = otherDayStart.isoformat() + 'Z'
    return otherDayStart
          
def otherDateEnd(until):
    otherDayEnd = datetime.datetime.utcnow().replace(hour=23, minute=59, second=59)
    otherDayEnd += datetime.timedelta(days=until)
    otherDayEnd = otherDayEnd.isoformat() + 'Z'
    return otherDayEnd

def newDate(day,hours,minutes):
    newDate = datetime.datetime.utcnow().replace(hour=hours, minute=minutes, second=01)
    newDate += datetime.timedelta(days=day)
    newDate = newDate.isoformat() + gmt
    newDate = parse_datetime_string(str(newDate))
    return newDate

def parse_datetime_string(string):
    # logger.info('Parsing '+string)
    if 'T' in string:
        return dateutil.parser.parse(string)
    else:
        return dateutil.parser.parse(string + " 00:00:00 LOC", tzinfos={"LOC": get_localzone()})

def checkLocation(eventDict):
    locationFlag = True if "location" in eventDict else False
    return locationFlag	

def checkDescription(eventDict):
    descriptionFlag = True if "description" in eventDict else False
    return descriptionFlag	

def getDateWeekday(weekday,eventHour):
    day_evaluate = weekday
    today = datetime.datetime.strptime(time.strftime("%x"),"%m/%d/%y")
    if ('am' in eventHour) or ('pm' in eventHour) or ('AM' in eventHour) or ('PM' in eventHour):
	start_hour = datetime.datetime.strptime(eventHour, "%I:%M %p").hour
    	start_minute = datetime.datetime.strptime(eventHour, "%I:%M %p").minute
    else:
	start_hour = datetime.datetime.strptime(eventHour, "%I:%M").hour
    	start_minute = datetime.datetime.strptime(eventHour, "%I:%M").minute

    for i in range(1,8):
	date = today + datetime.timedelta(days=i)
	day_name = date.strftime("%A")
	if (day_evaluate.upper() == day_name.upper()):
		date = date.replace(hour=start_hour, minute=start_minute)
		return date.isoformat() + gmt

def getEndHour(date,duration):
    start_date = date[:22]+date[(22+1):]
    if '+' in start_date:
	new_date = datetime.datetime.strptime(start_date,"%Y-%m-%dT%H:%M:%S+%f")
    else:
	new_date = datetime.datetime.strptime(start_date,"%Y-%m-%dT%H:%M:%S-%f")

    new_date = new_date + datetime.timedelta(hours=int(duration))
    return new_date.isoformat() + gmt

def getMonth(month):
    months = ["January","February","March","April","May","June","July","August","September","October","November","December"]
    return months.index(month)+1

def getDescription(word):
	hours_check= ["one ","two ","three ","four ","five ","six ","seven ","eight ","nine ","ten ","eleven ", \
                     "twelve ","thirteen ","fourteen ","fifteen ","sixteen ","seventeen ","eighteen ","nineteen ","twenty ", "am ","pm ", "AM ","PM "]
	found = False
	wordNew = word + " "
	if filter(lambda x: wordNew in x, hours_check):
		found = True
		global word_found
		wordNew = word + " "
		word_found = filter(lambda x: wordNew in x, hours_check)
	else:
		found = False
	return found

class GoogleCalendarSkill(MycroftSkill):
    """
    A Skill to check your google calendar
    also can add events
    """
    def google_calendar(self, msg=None):
	"""
    	Verify credentials to make google calendar connectionimport calendar
    	"""
	argv = sys.argv
        sys.argv = []
        self.credentials = get_credentials()
        http = self.credentials.authorize(httplib2.Http())
        self.service = discovery.build('calendar', 'v3', http=http)
	sys.argv = argv


    def eventJson(self,attendees_string,summary,start,end):
	event_json = {}
	attendees = []
	attendees_own = []
	attendees_family = []
	attendees_work = []


	msg = ""
	if (attendees_string.upper() == "OWN"):
		for i in range(len(attendees_own_Email)):
			email = {'email':attendees_own_Email[i]}
			attendees_own.append(email)
		attendees = attendees_own
		msg =  "Your appointment has been created."

	elif (attendees_string.upper() == "FAMILY"):
		for i in range(len(attendees_family_Email)):
			email = {'email':attendees_family_Email[i]}
			attendees_family.append(email)
		attendees = attendees_family
		msg =  "Your appointment whit your family group has been created."

	elif (attendees_string.upper() == "WORK"):
		for i in range(len(attendees_work_Email)):
			email = {'email':attendees_work_Email[i]}
			attendees_work.append(email)
		attendees = attendees_work
		msg =  "Your appointment whit your work group has been created."


	
	start_time = {"dateTime":start,"timeZone":timeZone }
	end_time = {"dateTime":end,"timeZone":timeZone }
	
	overrides = []

	overrides.append({'method':'email', 'minutes':email_minutes})
	overrides.append({'method':'popup', 'minutes':pop_up_minutes})
	
	event_json = {'summary':summary,'description':descAgent, 'sendNotifications':True, 'start':start_time,'end':end_time,'attendees':attendees,'reminders':{'useDefault':False, 'overrides':overrides}}

	"""
	Run add event to calendar outside Mycroft Virtual Environment 

    	"""
	addCalendar_cmd = python_out + " " + third_party_skill + "/addCalendar.py %r" % json.dumps(event_json)

	print os.popen(addCalendar_cmd).read()

	return msg



    def __init__(self):
        super(GoogleCalendarSkill, self).__init__('GoogleCalendarSkill')
    	"""
	Get the Google calandar parameters from config
	today = time.strftime("%Y-%m-%dT%H:%M:%S-06:00") for use on create event
	"""
	self.loginEnabled = self.config.get('loginEnabled')
	self.userLogin = self.config.get('userLogin')
	self.calendar_id = self.config.get('calendar_id')
	self.maxResults = self.config.get('maxResults')
	self.gmt = self.config.get('gmt')
	self.timeZone = self.config.get('timeZone')
	self.attendees_own = self.config.get('attendees_own')
	self.attendees_family = self.config.get('attendees_family')
	self.attendees_work = self.config.get('attendees_work')
	self.reminders_email = self.config.get('reminders_email')
	self.reminders_popup = self.config.get('reminders_popup')
	self.default_duration = self.config.get('default_duration')
	self.time_format = self.config.get('time_format')

	global attendees_own_Email
	global attendees_family_Email
	global attendees_work_Email

	global python_out
	global third_party_skill
	global effects

	global gmt
	global timeZone
	global email_minutes
	global pop_up_minutes 
	global event_duration	# In Hours
	gmt = self.gmt
	timeZone = self.timeZone
	email_minutes = self.reminders_email
	pop_up_minutes = self.reminders_popup
	event_duration = int(self.default_duration)

	loginEnabled = self.loginEnabled 
	
	attendees_own = self.attendees_own
	attendees_family = self.attendees_family
	attendees_work = self.attendees_work

	attendees_own_Email=[]
	attendees_own_Email = attendees_own.split(',')

	attendees_family_Email=[]
	attendees_family_Email = attendees_family.split(',')

	attendees_work_Email=[]
	attendees_work_Email = attendees_work.split(',')



    def get_time_format(self, convert_time):
        if self.format == 12:
            current_time = datetime.date.strftime(convert_time, "%I:%M, %p")
        else:
            current_time = datetime.date.strftime(convert_time, "%H:%M ")
        return current_time

    def get_timezone(self, locale):
        a = Astral()
        try:
            city = a[locale]
            return city.timezone
        except:
            return None


    def initialize(self):
    	"""
	Mycroft Google Calendar Intents
	"""

        self.load_data_files(dirname(__file__))
	self.load_regex_files(join(dirname(__file__), 'regex', 'en-us'))

        self.emitter.on(self.name + '.google_calendar',self.google_calendar)
        self.emitter.emit(Message(self.name + '.google_calendar'))

        intent = IntentBuilder('WhenEventsFutureIntent')\
            .require('WhenKeyword') \
            .require('IsKeyword') \
	    .require('Ask') \
            .build()
        self.register_intent(intent, self.handle_when_event_future)
	"""

        intent = IntentBuilder('WhenEventsFutureIntent')\
            .require('DateKeyword') \
            .require('OfKeyword') \
            .require('TheKeyword') \
            .build()
        self.register_intent(intent, self.handle_when_event_future)
	"""

	# *****************************************************
	# Add event Intent to Calendar Section
	# ***************************************************** //  .optionally('OnKeyword') \

        intent = IntentBuilder('AddMonthDayIntent')\
            .require('ScheduleKeyword') \
	    .optionally('CalendarGroupKeyword') \
            .require('EventKeyword') \
	    .require('MonthKeyword') \
	    .require('XDaysKeyword') \
	    .require('AtKeyword') \
	    .require('HoursKeyword') \
	    .optionally('AMPMKeyword') \
	    .optionally('Description') \
            .build()
        self.register_intent(intent, self.handle_add_month_day_event)

        intent = IntentBuilder('AddEventIntent')\
            .require('SetKeyword') \
	    .optionally('CalendarGroupKeyword') \
            .require('EventKeyword') \
	    .optionally('DateEventKeyword') \
	    .require('AtKeyword') \
	    .require('HoursKeyword') \
	    .optionally('AMPMKeyword') \
	    .optionally('Description') \
            .build()
        self.register_intent(intent, self.handle_add_event)

        intent = IntentBuilder('AddMonthDayStartEndIntent')\
            .require('ScheduleKeyword') \
	    .optionally('CalendarGroupKeyword') \
            .require('EventKeyword') \
	    .optionally('OnKeyword') \
	    .require('MonthKeyword') \
	    .require('XDaysKeyword') \
	    .require('FromKeyword') \
	    .require('HoursKeyword') \
	    .optionally('AMPMKeyword') \
	    .require('ToKeyword') \
	    .require('HoursEndKeyword') \
	    .optionally('AMPMEndKeyword') \
	    .optionally('Description') \
            .build()
        self.register_intent(intent, self.handle_add_month_start_end_event)

        intent = IntentBuilder('AddEventStartEndIntent')\
            .require('SetKeyword') \
    	    .optionally('CalendarGroupKeyword') \
            .require('EventKeyword') \
	    .optionally('DateEventKeyword') \
	    .require('FromKeyword') \
	    .require('HoursKeyword') \
	    .optionally('AMPMKeyword') \
	    .require('HoursEndKeyword') \
	    .optionally('AMPMEndKeyword') \
	    .optionally('Description') \
            .build()
        self.register_intent(intent, self.handle_add_start_end_event)

	# *****************************************************
	# Get events Intent from Calendar Section
	# *****************************************************
        intent = IntentBuilder('NextEventIntent')\
            .require('NextKeyword') \
            .require('EventKeyword') \
	    .optionally('WhereKeyword') \
            .build()
        self.register_intent(intent, self.handle_next_event)

        intent = IntentBuilder('WithEventIntent')\
            .require('EventKeyword') \
	    .require('Person') \
            .build()
        self.register_intent(intent, self.handle_with_event)

        intent = IntentBuilder('TodaysEventsIntent')\
	    .require('ForKeyword') \
            .require('TodayKeyword') \
            .require('EventKeyword') \
            .build()
        self.register_intent(intent, self.handle_today_events)

        intent = IntentBuilder('TomorrowEventsIntent')\
	    .require('ForKeyword') \
            .require('TomorrowKeyword') \
            .require('EventKeyword') \
            .build()
        self.register_intent(intent, self.handle_tomorrow_events)

        intent = IntentBuilder('UntilTomorrowEventsIntent')\
            .require('UntilTomorrowKeyword') \
            .require('EventKeyword') \
            .build()
        self.register_intent(intent, self.handle_until_tomorrow_events)

        intent = IntentBuilder('EventsForWeekDayIntent')\
	    .require('ForKeyword') \
            .require('WeekdayKeyword') \
            .require('EventKeyword') \
            .build()
        self.register_intent(intent, self.handle_weekday_events)

        intent = IntentBuilder('EventsForXDaysIntent')\
	    .require('FollowingsKeyword') \
	    .require('EventKeyword') \
            .require('XDaysKeyword') \
            .build()
        self.register_intent(intent, self.handle_xdays_events)


    def load_all_events(self, tMin=None, tMax=None):
        calendars = self.service.calendarList().list().execute()
        events = []
        for calendar in calendars['items']:
            eventsResult = self.service.events().list(
                calendarId=calendar['id'], timeMin=tMin, timeMax=tMax, maxResults=self.maxResults, singleEvents=True,
                orderBy='startTime').execute()
            events.extend(eventsResult.get('items'))
        events.sort(key=lambda x: parse_datetime_string(x['start'].get('dateTime', x['start'].get('date'))))
        return events

    def handle_next_event(self, message):
        brief = True
	if not loggedIn():
		self.speak_dialog('NotAccess')
		return

	where = message.data.get("WhereKeyword")
	if where == None:
		where = ""

	self.speak_dialog('VerifyCalendar')
        now = datetime.datetime.utcnow()
        localNow = datetime.datetime.now(get_localzone())
        # 'Z' indicates UTC time
        events = self.load_all_events(tMin=now.isoformat() + 'Z')

        if not events:
            self.speak_dialog('NoEvents')
        else:
            # Events from the past that are still going on will be in here.
            # Skip down to the appointment that really comes next.
            nextEvent = None
            start = None
            place = ''
	    description = ''
            for event in events:
                nextEvent = event
                start = event['start'].get('dateTime', event['start'].get('date'))
	        start = start[:22]+start[(22+1):]
            #    logger.info('Considering event: '+ event.get('summary', 'busy') + ' ' + start)
            for event in events:
                nextEvent = event
                start = event['start'].get('dateTime', event['start'].get('date'))
	        start = start[:22]+start[(22+1):]
	        start = parse_datetime_string(start)
                if (start >= localNow):
                   break

            if (start < localNow):
                self.speak_dialog('NoEvents')
                return

	    today = datetime.datetime.strptime(time.strftime("%x"),"%m/%d/%y") 
    	    tomorrow = today + datetime.timedelta(days=1)
	    date_compare = datetime.datetime.strptime(start.strftime("%x"),"%m/%d/%y")

	    rangeDate = "today"
	    if (date_compare == today):
		rangeDate = "today"
	    elif (date_compare == tomorrow):
	    	rangeDate = "tomorrow"
	    else:
		month_name = (calendar.month_name[start.month])
		day_name = (calendar.day_name[start.weekday()])
		day = str(start.day)
		rangeDate = day_name + ", " + month_name + " " + day

	    startHour = ("{:d}:{:02d}".format(start.hour, start.minute))
	    startHour = time.strptime(startHour,"%H:%M")
	    startHour = time.strftime("%I:%M %p",startHour)
	    if (startHour[0]=='0'): startHour = startHour.replace('0','',1)
	    end = event['end'].get('dateTime', event['end'].get('date'))
	    end = end[:22]+end[(22+1):]
	    end = parse_datetime_string(end)
	    endHour = ("{:d}:{:02d}".format(end.hour, end.minute))
	    endHour = time.strptime(endHour,"%H:%M")
	    endHour = time.strftime("%I:%M %p",endHour)
	    if (endHour[0]=='0'): endHour = endHour.replace('0','',1)

	    complete_phrase = ""
	    if (checkLocation(event)):
	    	location = event['location']
	    	location = location.splitlines()
	    	place_city = ','.join(location[:1])
		place =  " on " + place_city 
	    else:
		place =  ""

	    organizer = event['organizer']
	    status = event['status']
	    summary = event.get('summary', 'busy')

    	    if (checkDescription(event) and not brief):
		description = event['description'] 
	    else:
		description = ''
 
	    if (len(organizer)) == 2:
		organizer = organizer['displayName']
		if (where.upper() == "WHERE"):
			if (len(place) > 3):
				complete_phrase = "Your next appointment will be" + place + " organized by " + organizer + " "
				place = ""
			else:
				complete_phrase = "There is not detailed place, but " + organizer + " has scheduled a appointment for "
		else:
			complete_phrase = organizer + " has scheduled a appointment for "

		complete_phrase = complete_phrase + rangeDate  + " begining at " + startHour + " and ending at " + endHour + place
		complete_phrase = complete_phrase + ". About " + summary + ". " + description

	    elif (len(organizer)) == 3:
		if (where.upper() == "WHERE"):
			if (len(place) > 3):
				complete_phrase = "Your next appointment will be" + place + " "
				place = ""
			else:
				complete_phrase = "There is not detailed place, but you have a appointment "
		else:
			complete_phrase = "You have a appointment "

		complete_phrase = complete_phrase + rangeDate  + " from " + startHour + " until " + endHour + " at " + place 
		complete_phrase = complete_phrase + ". About " + summary + ". " + description

	    self.speak(complete_phrase)


    def handle_with_event(self, message):
	if not loggedIn():
		self.speak_dialog('NotAccess')
		return

	person = message.data.get("Person", None)
        now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates Uprint ("****** Start Key",StartKeyword)TC time
	weekDayName = ""	# It's not necesary on this handle
        self.until_events(now, otherDateEnd(30),30, person)

    def handle_today_events(self, msg=None):
	if not loggedIn():
		self.speak_dialog('NotAccess')
		return

        now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates Uprint ("****** Start Key",StartKeyword)TC time
	weekDayName = ""	# It's not necesary on this handle
        self.until_events(now, todayDateEnd(),0, weekDayName)

    def handle_tomorrow_events(self, msg=None):
	if not loggedIn():
		self.speak_dialog('NotAccess')
		return
	weekDayName = ""	# It's not necesary on this handle
        self.until_events(tomorrowDateStart(), tomorrowDateEnd(),1, weekDayName)

    def handle_until_tomorrow_events(self, msg=None):
	if not loggedIn():
		self.speak_dialog('NotAccess')
		return
        now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates Uprint ("****** Start Key",StartKeyword)TC time
	weekDayName = ""	# It's not necesary on this handle
        self.until_events(now, tomorrowDateEnd(),2, weekDayName)

    def handle_weekday_events(self, message):
	if not loggedIn():
		self.speak_dialog('NotAccess')
		return
	# Calculate in range from the day after tomorrow plus 7 days 
	weekDayName = message.data.get("WeekdayKeyword")
	self.until_events(otherDateStart(2), otherDateEnd(8),7, weekDayName)

    def handle_xdays_events(self, message):
	if not loggedIn():
		self.speak_dialog('NotAccess')
		return
	XDayAfter = message.data.get("XDaysKeyword")
        now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
	weekDayName = ""	# It's not necesary on this handle
        self.until_events(now, otherDateEnd(int(XDayAfter)),int(XDayAfter), weekDayName)

    def until_events(self, startDate, stopDate, rangeDays, weekDayName, brief=True):
	self.speak_dialog('VerifyCalendar')
	person = ""
	eventWith = False
	evaluatePerson = False
	if ( len(weekDayName) > 1):
		evaluateWeekDay = False
		evaluatePerson = False
		if (weekDayName.upper() == "SUNDAY") or (weekDayName.upper() == "MONDAY") or (weekDayName.upper() == "TUESDAY") or (weekDayName.upper() == "WEDNESDAY") or (weekDayName.upper() == "THURSDAY") or (weekDayName.upper() == "FRIDAY") or (weekDayName.upper() == "SATURDAY") :
			evaluateWeekDay = True
			evaluatePerson = False
		else :
			evaluatePerson = True
			evaluateWeekDay = False
			person = weekDayName
	else:
		evaluateWeekDay = False

        events = self.load_all_events(tMin=startDate, tMax=stopDate)

	today = datetime.datetime.strptime(time.strftime("%x"),"%m/%d/%y") 
    	tomorrow = today + datetime.timedelta(days=1)
    	other_date = today + datetime.timedelta(days=rangeDays)

        if not events:
		self.speak_dialog('NoEvents')
        else:
		for event in events:
			start = event['start'].get('dateTime', event['start'].get('date'))
			start = start[:22]+start[(22+1):]
			start = parse_datetime_string(start)
			date_compare = datetime.datetime.strptime(start.strftime("%x"),"%m/%d/%y")
	    		startHour = ("{:d}:{:02d}".format(start.hour, start.minute))
	    		startHour = time.strptime(startHour,"%H:%M")
	    		startHour = time.strftime("%I:%M %p",startHour)
	    		if (startHour[0]=='0'): startHour = startHour.replace('0','',1)
	    		end = event['end'].get('dateTime', event['end'].get('date'))
	    		end = end[:22]+end[(22+1):]
			end = parse_datetime_string(end)
	    		endHour = ("{:d}:{:02d}".format(end.hour, end.minute))
	    		endHour = time.strptime(endHour,"%H:%M")
	    		endHour = time.strftime("%I:%M %p",endHour)
	    		if (endHour[0]=='0'): endHour = endHour.replace('0','',1)
	    		if (checkLocation(event)):
	    			location = event['location']
	    			location = location.splitlines()
	    			place_city = ','.join(location[:1])
				place =  " on " + place_city 
	    		else:
				place =  ""
	    		organizer = event['organizer']
			if (len(organizer)) == 2:
				phrase_part_1= organizer['displayName'] + " has scheduled a appointment for "
				phrase_part_2= " from " + startHour + " until " + endHour + place
			elif (len(organizer)) == 3:
				phrase_part_1 = "You have a appointment "
				phrase_part_2= ", from " + startHour + " until " + endHour + " at " + place 

	    		status = event['status']
	    		summary = event['summary']

    	    		if (checkDescription(event) and not brief):
				description = event['description'] 
	    		else:
				description = ''

			phrase_part_3= ". About " + summary + ". " + description

			if (rangeDays == 0):		# compare the same day
				if (date_compare == today):
					rangeDate = "today"		
					complete_phrase = phrase_part_1 + rangeDate  + phrase_part_2 + phrase_part_3
	    				self.speak(complete_phrase)

			elif (rangeDays == 1 ):		# compare the next dayadd new event from 8:30 am to 11:45 am almuerzo con Gianluca despues de la fundacion
				if (date_compare == tomorrow):
					rangeDate = "tomorrow"		
					complete_phrase = phrase_part_1 + rangeDate  + phrase_part_2 + phrase_part_3
	    				self.speak(complete_phrase)

			elif (rangeDays == 2 ):		# compare until the next day
				if (date_compare <= tomorrow):
					rangeDate = "today"
					if (date_compare == today):
						rangeDate = "today"
					elif (date_compare == tomorrow):
						rangeDate = "tomorrow"
					complete_phrase = phrase_part_1 + rangeDate  + phrase_part_2 + phrase_part_3
					self.speak(complete_phrase)

			elif (evaluateWeekDay):		# compare the day name
				day_name_compare = (calendar.day_name[start.weekday()])
				if (day_name_compare.upper() == weekDayName.upper()):
					day = str(start.day)
					month_name = (calendar.month_name[start.month])
					rangeDate = weekDayName + ", " + month_name + " " + day
					complete_phrase = phrase_part_1 + rangeDate  + phrase_part_2 + phrase_part_3
					self.speak(complete_phrase)

			elif (evaluatePerson):		# find a person name on summary
				if person.upper() in summary.upper():
					rangeDate = "today"
					if (date_compare == today):
						rangeDate = "today"
					elif (date_compare == tomorrow):
						rangeDate = "tomorrow"
					else:
						month_name = (calendar.month_name[start.month])
						day_name = (calendar.day_name[start.weekday()])
						day = str(start.day)
						rangeDate = day_name + ", " + month_name + " " + day
				
					complete_phrase = phrase_part_1 + " with " + person + " " + rangeDate  + phrase_part_2 + phrase_part_3
					self.speak(complete_phrase)
					eventWith = True

			elif (rangeDays >2 ):		# compare until the nexts x days
				if (date_compare <= other_date):
					rangeDate = "today"
					if (date_compare == today):
						rangeDate = "today"
					elif (date_compare == tomorrow):
						rangeDate = "tomorrow"
					else:
						month_name = (calendar.month_name[start.month])
						day_name = (calendar.day_name[start.weekday()])
						day = str(start.day)
						rangeDate = day_name + ", " + month_name + " " + day

					complete_phrase = phrase_part_1 + rangeDate  + phrase_part_2 + phrase_part_3
					self.speak(complete_phrase)
			
		if not eventWith and evaluatePerson :
			self.speak("You have not scheduled appointments with " + person + " in the next " + str(rangeDays) + " days")


    def handle_add_month_day_event(self, message):
	if not loggedIn():
		self.speak_dialog('NotAccess')
		return

	set_key = message.data.get("SetKeyword")
	calendarGroup = message.data.get("CalendarGroupKeyword")
	event_key = message.data.get("EventKeyword")
	event_date = message.data.get("MonthKeyword")
	number_day = message.data.get("XDaysKeyword")
	hour = message.data.get("HoursKeyword")
	ampm = message.data.get("AMPMKeyword")
	description = message.data.get("Description")
	message_complete = message.data

	if (":" in hour):
		hour = hour
	else:
		hour = hour + ":00"

	if "CalendarGroupKeyword" in message_complete:
		if calendarGroup.upper() == "MY" or calendarGroup.upper() == "MINE" or calendarGroup.upper() == "OWN" :
			calendarGroup = "OWN"
		else:
			calendarGroup = calendarGroup.upper()
		
	else:
		calendarGroup = "OWN"



	if "AMPMKeyword" in message_complete:
		hour = hour + " " + ampm
	else:
		description = message.data.get("utterance").split('at ')[1]
		hourT = description[:5]
		if (":" in hourT):
			hour = description[:5]
			description = description[6:]
		else:  
			description = message.data.get("utterance").split('at ')[1]
			word_string = description.split(' ') 
			for i in range(0,len(word_string)):
				word = word_string[i]
				found = getDescription(word)

			found=word_found[0]
			description = description.split(found)[1]

		hour = time.strptime(hour, "%H:%M")
		hour = time.strftime("%I:%M %p",hour)

	if description is None:
		description = message.data.get("utterance").split('at ')[1]
		word_string = description.split(' ') 
		for i in range(0,len(word_string)):
			word = word_string[i]
			found = getDescription(word)

		found=word_found[0]
		description = description.split(found)[1]

	current_year = datetime.datetime.now().strftime("%Y")

	if (event_date.upper() == "JANUARY") or (event_date.upper() == "FEBRUARY") or (event_date.upper() == "MARCH") or (event_date.upper() == "APRIL") or (event_date.upper() == "MAY") or (event_date.upper() == "JUNE") or (event_date.upper() == "JULY") or (event_date.upper() == "AUGUST") or (event_date.upper() == "SEPTEMBER") or (event_date.upper() == "OCTOBER") or (event_date.upper() == "NOVEMBER") or (event_date.upper() == "DECEMBER") :
		from_month = getMonth(event_date)
		from_date = str(current_year)+"-"+str(from_month)+"-"+number_day
		
		start_hour = datetime.datetime.strptime(hour, "%I:%M %p").hour
    		start_minute = datetime.datetime.strptime(hour, "%I:%M %p").minute

		from_date = datetime.datetime.strptime(from_date,"%Y-%m-%d")

		if (from_date <= datetime.datetime.utcnow()):
			from_date = from_date.replace(year=int(current_year)+1)

		from_date = from_date.replace(hour=start_hour, minute=start_minute)
		from_date = from_date.isoformat() + gmt

		to_date = getEndHour(from_date,event_duration)
		addCalendar = self.eventJson(calendarGroup,description,str(from_date),str(to_date))
		self.speak(addCalendar)



    def handle_add_event(self, message):
	if not loggedIn():
		self.speak_dialog('NotAccess')
		return

	set_key = message.data.get("SetKeyword")
	calendarGroup = message.data.get("CalendarGroupKeyword")
	event_key = message.data.get("EventKeyword")
	event_date = message.data.get("DateEventKeyword")
	hour = message.data.get("HoursKeyword")
	ampm = message.data.get("AMPMKeyword")
	description = message.data.get("Description")
	message_complete = message.data

	if event_date is None:
		event_date = "TODAY"

	if (":" in hour):
		hour = hour
	else:
		hour = hour + ":00"

	if "CalendarGroupKeyword" in message_complete:
		if calendarGroup.upper() == "MY" or calendarGroup.upper() == "MINE" or calendarGroup.upper() == "OWN" :
			calendarGroup = "OWN"
		else:
			calendarGroup = calendarGroup.upper()
		
	else:
		calendarGroup = "OWN"


	if "AMPMKeyword" in message_complete:
		hour = hour + " " + ampm
	else:
		description = message.data.get("utterance").split('at ')[1]
		hourT = description[:5]
		if (":" in hourT):
			hour = description[:5]
			description = description[6:]
		else:  
			description = message.data.get("utterance").split('at ')[1]
			word_string = description.split(' ') 
			for i in range(0,len(word_string)):
				word = word_string[i]
				found = getDescription(word)

			found=word_found[0]
			description = description.split(found)[1]

		hour = time.strptime(hour, "%H:%M")
		hour = time.strftime("%I:%M %p",hour)

	if description is None:
		description = message.data.get("utterance").split('at ')[1]
		word_string = description.split(' ') 
		for i in range(0,len(word_string)):
			word = word_string[i]
			found = getDescription(word)

		found=word_found[0]
		description = description.split(found)[1]


	current_year = datetime.datetime.now().strftime("%Y")
	current_month = datetime.datetime.now().strftime("%m")
	today = datetime.datetime.now().strftime("%d")
	tomorrow = int(today) + 1

	start_hour = datetime.datetime.strptime(hour, "%I:%M %p").hour
	start_minute = datetime.datetime.strptime(hour, "%I:%M %p").minute

	if (event_date.upper() == "TODAY"):
		from_date = str(current_year)+"-"+str(current_month)+"-"+str(today)
	elif (event_date.upper() == "TOMORROW"):
		from_date = str(current_year)+"-"+str(current_month)+"-"+str(tomorrow)
	elif (event_date.upper() == "SUNDAY") or (event_date.upper() == "MONDAY") or (event_date.upper() == "TUESDAY") or (event_date.upper() == "WEDNESDAY") or (event_date.upper() == "THURSDAY") or (event_date.upper() == "FRIDAY") or (event_date.upper() == "SATURDAY") :
		from_date = getDateWeekday(event_date, hour)
		from_date = from_date[:22]+from_date[(22+1):]
		if '+' in from_date:
			from_date= datetime.datetime.strptime(from_date,"%Y-%m-%dT%H:%M:%S+%f")
    		else:
			from_date= datetime.datetime.strptime(from_date,"%Y-%m-%dT%H:%M:%S-%f")

		weekday_year = from_date.year
		weekday_month = from_date.month
		weekday_day = from_date.day
		from_date = str(weekday_year)+"-"+str(weekday_month)+"-"+str(weekday_day)

	from_date = datetime.datetime.strptime(from_date,"%Y-%m-%d")
	from_date = from_date.replace(hour=start_hour, minute=start_minute)

	from_date = from_date.isoformat() + gmt

	to_date = getEndHour(from_date,event_duration)
	addCalendar = self.eventJson(calendarGroup,description,str(from_date),str(to_date))
	self.speak(addCalendar)

    def handle_add_start_end_event(self, message):
	if not loggedIn():
		self.speak_dialog('NotAccess')
		return

	set_key = message.data.get("SetKeyword")
	calendarGroup = message.data.get("CalendarGroupKeyword")
	event_key = message.data.get("EventKeyword")
	from_key = message.data.get("FromKeyword")
	event_date = message.data.get("DateEventKeyword")
	hourStart = message.data.get("HoursKeyword")
	ampmStart = message.data.get("AMPMKeyword")
	hourEnd = message.data.get("HoursEndKeyword")
	ampmEnd = message.data.get("AMPMEndKeyword")
	description = message.data.get("Description")
	message_complete = message.data

	if event_date is None:
		event_date = "TODAY"

	if (":" in hourStart):
		hourStart = hourStart
	else:
		hourStart = hourStart + ":00"

	if (":" in hourEnd):
		hourEnd = hourEnd
	else:
		hourEnd = hourEnd + ":00"

	if "CalendarGroupKeyword" in message_complete:
		if calendarGroup.upper() == "MY" or calendarGroup.upper() == "MINE" or calendarGroup.upper() == "OWN" :
			calendarGroup = "OWN"
		else:
			calendarGroup = calendarGroup.upper()
		
	else:
		calendarGroup = "OWN"


	if "AMPMKeyword" in message_complete:
		hourStart = hourStart + " " + ampmStart
		hourEnd = hourEnd + " " + ampmEnd
	else:
		description = message.data.get("utterance").split('to ')[1]
		hourT = description[:5]
		if (":" in hourT):
			hour = description[:5]
			description = description[6:]
		else:  
			description = message.data.get("utterance").split('to ')[1]
			word_string = description.split(' ') 
			for i in range(0,len(word_string)):
				word = word_string[i]
				found = getDescription(word)

			found=word_found[0]
			description = description.split(found)[1]

		hourStart = time.strptime(hourStart, "%H:%M")
		hourStart = time.strftime("%I:%M %p",hourStart)
		hourEnd = time.strptime(hourEnd, "%H:%M")
		hourEnd = time.strftime("%I:%M %p",hourEnd)


	if description is None:
		description = message.data.get("utterance").split('to ')[1]
		word_string = description.split(' ') 
		for i in range(0,len(word_string)):
			word = word_string[i]
			found = getDescription(word)

		found=word_found[0]
		description = description.split(found)[1]

	current_month = datetime.datetime.now().strftime("%m")
	current_year = datetime.datetime.now().strftime("%Y")
	today = datetime.datetime.now().strftime("%d")
	tomorrow = int(today) + 1

	start_hour_h = datetime.datetime.strptime(hourStart, "%I:%M %p").hour
	start_hour_m = datetime.datetime.strptime(hourStart, "%I:%M %p").minute

	end_hour_h = datetime.datetime.strptime(hourEnd, "%I:%M %p").hour
	end_hour_m = datetime.datetime.strptime(hourEnd, "%I:%M %p").minute

	if (event_date.upper() == "TODAY"):
		from_date = str(current_year)+"-"+str(current_month)+"-"+str(today)
		to_date = from_date
	elif (event_date.upper() == "TOMORROW"):
		from_date = str(current_year)+"-"+str(current_month)+"-"+str(tomorrow)
		to_date = from_date
	elif (event_date.upper() == "SUNDAY") or (event_date.upper() == "MONDAY") or (event_date.upper() == "TUESDAY") or (event_date.upper() == "WEDNESDAY") or (event_date.upper() == "THURSDAY") or (event_date.upper() == "FRIDAY") or (event_date.upper() == "SATURDAY") :
		from_date = getDateWeekday(event_date, hourStart)
		from_date = from_date[:22]+from_date[(22+1):]
		if '+' in from_date:
			from_date= datetime.datetime.strptime(from_date,"%Y-%m-%dT%H:%M:%S+%f")
    		else:
			from_date= datetime.datetime.strptime(from_date,"%Y-%m-%dT%H:%M:%S-%f")

		weekday_year = from_date.year
		weekday_month = from_date.month
		weekday_day = from_date.day
		from_date = str(weekday_year)+"-"+str(weekday_month)+"-"+str(weekday_day)
		to_date = from_date

	from_date = datetime.datetime.strptime(from_date,"%Y-%m-%d")
	from_date = from_date.replace(hour=start_hour_h, minute=start_hour_m)
	from_date = from_date.isoformat() + gmt

	to_date = datetime.datetime.strptime(to_date,"%Y-%m-%d")
	to_date = to_date.replace(hour=end_hour_h, minute=end_hour_m)
	to_date = to_date.isoformat() + gmt

	addCalendar = self.eventJson(calendarGroup,description,str(from_date),str(to_date))
	self.speak(addCalendar)


    def handle_add_month_start_end_event(self, message):
	if not loggedIn():
		self.speak_dialog('NotAccess')
		return

	set_key = message.data.get("ScheduleKeyword")
	calendarGroup = message.data.get("CalendarGroupKeyword")
	event_key = message.data.get("EventKeyword")
	on_key = message.data.get("OnKeyword")
	event_date = message.data.get("MonthKeyword")
	number_day = message.data.get("XDaysKeyword")
	from_key = message.data.get("FromKeyword")
	hourStart = message.data.get("HoursKeyword")
	ampmStart = message.data.get("AMPMKeyword")
	hourEnd = message.data.get("HoursEndKeyword")
	ampmEnd = message.data.get("AMPMEndKeyword")
	description = message.data.get("Description")
	message_complete = message.data

	if event_date is None:
		event_date = "TODAY"

	if (":" in hourStart):
		hourStart = hourStart
	else:
		hourStart = hourStart + ":00"

	if (":" in hourEnd):
		hourEnd = hourEnd
	else:
		hourEnd = hourEnd + ":00"

	
	if "CalendarGroupKeyword" in message_complete:
		if calendarGroup.upper() == "MY" or calendarGroup.upper() == "MINE" or calendarGroup.upper() == "OWN" :
			calendarGroup = "OWN"
		else:
			calendarGroup = calendarGroup.upper()
		
	else:
		calendarGroup = "OWN"

	if "AMPMKeyword" in message_complete:
		hourStart = hourStart + " " + ampmStart
		hourEnd = hourEnd + " " + ampmEnd
	else:
		description = message.data.get("utterance").split('to ')[1]
		hourT = description[:5]
		if (":" in hourT):
			hour = description[:5]
			description = description[6:]
		else:  
			description = message.data.get("utterance").split('to ')[1]
			word_string = description.split(' ') 
			for i in range(0,len(word_string)):
				word = word_string[i]
				found = getDescription(word)

			found=word_found[0]
			description = description.split(found)[1]

		hourStart = time.strptime(hourStart, "%H:%M")
		hourStart = time.strftime("%I:%M %p",hourStart)
		hourEnd = time.strptime(hourEnd, "%H:%M")
		hourEnd = time.strftime("%I:%M %p",hourEnd)

	if description is None:
		description = message.data.get("utterance").split('to ')[1]
		word_string = description.split(' ') 
		for i in range(0,len(word_string)):
			word = word_string[i]
			found = getDescription(word)

		found=word_found[0]
		description = description.split(found)[1]


	current_year = datetime.datetime.now().strftime("%Y")

	if (event_date.upper() == "JANUARY") or (event_date.upper() == "FEBRUARY") or (event_date.upper() == "MARCH") or (event_date.upper() == "APRIL") or (event_date.upper() == "MAY") or (event_date.upper() == "JUNE") or (event_date.upper() == "JULY") or (event_date.upper() == "AUGUST") or (event_date.upper() == "SEPTEMBER") or (event_date.upper() == "OCTOBER") or (event_date.upper() == "NOVEMBER") or (event_date.upper() == "DECEMBER") :
		from_month = getMonth(event_date)
		from_date = str(current_year)+"-"+str(from_month)+"-"+number_day
		
		start_hour_h = datetime.datetime.strptime(hourStart, "%I:%M %p").hour
		start_hour_m = datetime.datetime.strptime(hourStart, "%I:%M %p").minute

		end_hour_h = datetime.datetime.strptime(hourEnd, "%I:%M %p").hour
		end_hour_m = datetime.datetime.strptime(hourEnd, "%I:%M %p").minute

		from_date = datetime.datetime.strptime(from_date,"%Y-%m-%d")
		if (from_date <= datetime.datetime.utcnow()):
			from_date = from_date.replace(year=int(current_year)+1)

		to_date = from_date
		from_date = from_date.replace(hour=start_hour_h, minute=start_hour_m)
		from_date = from_date.isoformat() + gmt

		to_date = to_date.replace(hour=end_hour_h, minute=end_hour_m)
		to_date = to_date.isoformat() + gmt

		addCalendar = self.eventJson(calendarGroup,description,str(from_date),str(to_date))
		self.speak(addCalendar)


    def handle_when_event_future(self, message):
	if not loggedIn():
		self.speak_dialog('NotAccess')
		return

	#when_key = message.data.get("WhenKeyword")
	ask_word = message.data.get("utterance")

	logger.info('***** WHEN EVENT ='+ask_word)


	if ("end of the world" in ask_word) or ("apocalypse" in ask_word) or ("final of the world" in ask_word) :
		play_mp3(effects+"end_of_world.mp3")
		time.sleep(36)
		self.speak_dialog('EndOfWorld')
	elif ("judgment day" in ask_word) or ("judgement day" in ask_word):
		play_mp3(effects+"judgment_day.mp3")
		time.sleep(16)
		self.speak_dialog('JudgmentDay')



def create_skill():
    return GoogleCalendarSkill()
