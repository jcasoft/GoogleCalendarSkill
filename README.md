**GoogleCalendarSkill with add events **
===================

For Mycroft
An skill to use with Mycroft which allow to interact with google calendar.
Now is possible to add events with a lot of intents

----------



Install Using MSM (Mycroft Skill Manager)  not for Mark1
-------------------

    msm install https://github.com/jcasoft/GoogleCalendarSkill.git


If it does not work with the MSM method try it with the manual method
For install in Mark1 use Manual Method on Mark1
of Manual Method not for Mark1

Manual Method not for Mark1
-------------------

    cd  /opt/mycroft/skills
    git clone https://github.com/jcasoft/GoogleCalendarSkill.git
    workon mycroft (Only if you have installed Mycroft on Virtualenv)
    pip install -r requirements.txt


Authorize Google Calendar not for Mark1
-------------------

Authorize Google Calendar Skill in distro with local web browser, wait web browse open and select "Allow"

    From your command line go to mycroft skills folder

    cd  /opt/mycroft/skills
    workon mycroft
    python GoogleCalendarSkill


Edit your ~/.mycroft/mycroft.conf

on "GoogleCalendarSkill" section (added automatically)



Manual Method for Mark1
-------------------

    cd  /opt/mycroft/skills
    git clone https://github.com/jcasoft/GoogleCalendarSkill.git
    pip install -r requirements.txt


Authorize Google Calendar for Mark1
-------------------
	
Authorize GoogleCalendarSkill in Mark1 without local web browser

    open SSH session

    From your command line go to mycroft skills folder

    cd  /opt/mycroft/skills
    python GoogleCalendarSkill --noauth_local_webserver

Open the generated link in computer with browser and wait the verification code and paste

     Enter verification code: 4/oxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx   


The installation process generates automatically the file ~/.mycroft/mycroft.conf and ~/.credentials/mycroft-googlecalendar-skill.json


Then copy the following files and fix the permissions

     sudo mkdir /home/mycroft/.credentials
     sudo cp /home/pi/.credentials/mycroft-googlecalendar-skill.json /home/mycroft/.credentials/mycroft-googlecalendar-skill.json
     sudo chmod -R 777 /home/mycroft/.credentials

     sudo cp /home/pi/.mycroft/mycroft.conf /home/mycroft/.mycroft/mycroft.conf
     sudo chmod -R 777 /home/pi/.mycroft

Edit your ~/.mycroft/mycroft.conf with sudo (sudo nano ~/.mycroft/mycroft.conf)
on "GoogleCalendarSkill"  edit your options


Restart Mycroft

./stop-mycroft.sh

./start-mycroft.sh debug



----------

Features
--------------------

Currently this skill can do the following things to get information from your calendar (with some variation):

- Whats my next meeting
- List my appointments for today
- List my events for tomorrow
- List my appointments until tomorrow
- My compromises for the Sunday
- Whats my events for the following 5 days
- when is my appointment with gianluca
- Where is my next meeting


> **Note:**

> - The name of the day of the week intent, will be calculated from the next day until the same day of the following week
> - You can toggle key word with:
> - Next, today, tomorrow, until tomorrow, name of the day of the week , from 2 until 30 for the following X days.
> - Events, Events, Meeting, Mettings, Appointmen, Appointmens, Schedule, Scheduled, Compromise, Compromises


New Features: Add Events
--------------------

Currently this skill can do the following things to set events to your calendar (with some variation):

- Add new event tomorrow from 2:30 pm to 4:45 pm Lunch with Gianluca on Olive Gardens
- Set compromise today from 18:30 to 21:45 Dinner whit Gianluca after work
- Add new appointment from 8:30 am to 11:45 am Marketing planification
- Add new event friday from 11:30 am to 5:45 pm birthday party on carlos house

- Schedule meeting on march 2 from 8:30 am to 11:45 am Support team planification
- Schedule my meeting on october 25 from 8:30 am to 11:45 am Halloween party planification
- Schedule family meeting on november 2 from 1:30 pm to 5:45 pm New years party planification
- Schedule work meeting on january 13 from 13:30 to 16:45  Sales planification with customers
- Schedule meeting on march 2 at 18:30 Visit Carlos at Hospital

- Set event today at 7:45 pm Dinner with Gianluca
- Set event tomorrow at 7:45 am Breakfast with Gianluca
- Set event at 13:45 Lunch with Gianluca
- Set event saturday at 11:30 PM New years party planification


> **Note:**

> - For add events, you have to use hours with fractions of 15 minutes (Like: 10:15 am , 15.45 , 20:30 )
> - You can toggle key word with:
> - Today, tomorrow, name of the day of the week , month and day
> - Events, Events, Meeting, Mettings, Appointmen, Appointmens, Schedule, Scheduled, Compromise, Compromises



**Enjoy !**
--------
