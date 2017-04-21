"""
Google Calendar Alexa Skill:
-----------------------------
    Alexa reads from a json api link your public google calendar.
    Sort and group the reminders for each day.
    Alexa reads the sorted list.
"""
import requests
import logging
import datetime
import calendar
from flask import Flask, json
from flask_ask import Ask, question, statement, logger
from calendar import weekday, day_name

app = Flask(__name__)
ask = Ask(app, "/")
logging.getLogger('flask_ask').setLevel(logging.DEBUG)


def get_reminders():
    """
    Get reminders from a public google calendar.
    :return: A sorted list with reminders.
    """
    reminders_list = []
    request = requests.Session()
    url = 'https://www.googleapis.com/calendar/v3/calendars/' + \
          'fsdet2017@gmail.com/events?alwaysIncludeEmail=true&key=' + \
          'AIzaSyAu4LrLeEWF_3TWg4Mg2VNp5W0pmWVtW1w'
    response = request.get(url)
    data = response.json()
    now = str(datetime.datetime.now())
    for item in data["items"]:
        reminder_start = item["start"]["dateTime"]
        date_start = reminder_start[0:10]
        date_time = date_start + " " + reminder_start[11:16]
        if now > date_time:
            continue
        year_start = reminder_start[0:4]
        month_start = calendar.month_name[int(reminder_start[5:7])]
        day_start = reminder_start[8:10]
        day_number = weekday(int(year_start), int(reminder_start[5:7]),
                             int(day_start))
        day_name_start = day_name[day_number]
        time_start = change_time(reminder_start[11:16])
        reminder_end = item["end"]["dateTime"]
        date_end = reminder_end[0:10]
        year_end = reminder_end[0:4]
        month_end = calendar.month_name[int(reminder_end[5:7])]
        day_end = reminder_end[8:10]
        day_number = weekday(int(year_end), int(reminder_end[5:7]),
                             int(day_end))
        day_name_end = calendar.day_name[day_number]
        time_end = change_time(reminder_end[11:16])
        reminder = [item["summary"], date_start,
                    day_name_start, day_start, month_start, year_start,
                    time_start, date_end, day_name_end, day_end, month_end,
                    year_end, time_end]
        reminders_list.append(reminder)
    # sort by time
    reminders_list.sort(key=lambda reminder: reminder[6])
    # sort by date
    reminders_list.sort(key=lambda reminder: datetime.datetime.strptime(
        reminder[1], '%Y-%m-%d'))
    return reminders_list


def change_time(time):
    """
    Change time from 24-hours to 12-hour.
    :param time: time in a 24 hour form.
    :return: time in a 12 hour form.
    """
    hour = int(time[0:2])
    if hour > 12:
        return str(hour % 12) + ":" + time[3:5] + " PM"
    elif hour == 12:
        return str(hour) + ":" + time[3:5] + " PM"
    elif hour == 00:
        return "00:" + time[3:5] + " AM"
    else:
        return str(hour) + ":" + time[3:5] + " AM"


def classify_days(reminders_list):
    """
    Group the reminders by day and hour.
    :param reminders_list: Sorted list with reminders from calendar
    :return: Text with reminders from Google Calendar.
    """
    reminders = {}
    for reminder in reminders_list:
        key = reminder[2] + ", " + reminder[3] + ", " + reminder[4] + ", " + \
              reminder[5]
        if key not in reminders.keys():
            reminders[key] = [[reminder[0], reminder[1], reminder[6],
                               reminder[7], reminder[8], reminder[9],
                               reminder[10], reminder[11], reminder[12]]]
        else:
            reminders[key].append([reminder[0], reminder[1], reminder[6],
                                   reminder[7], reminder[8], reminder[9],
                                   reminder[10], reminder[11], reminder[12]])
    return reminders


def all_calendar(reminders_list):
    speech = ""
    for day, reminders in reminders_list.items():
        speech += "Day " + day + ", "
        for reminder in reminders:
            # if start day == end day
            if reminder[1] == reminder[3]:
                speech += "Reminder, '" + reminder[0] + "', from " + \
                          reminder[2] + " to " + reminder[-1] + ". "
            else:
                speech += "Reminder, '" + reminder[0] + "', from " + \
                          reminder[2] + " to " + reminder[4] + ", " + \
                          reminder[5] + ", " + reminder[6] + ", " + \
                          reminder[7] + " at " + reminder[-1] + ". "
    return speech


def specific_day(get_day, reminders_list):
    speech = ""
    for day, reminders in reminders_list.items():
        if reminders[0][1] == get_day:
            speech += "Day " + day + ", "
            for reminder in reminders:
                # if start day == end day
                if reminder[1] == reminder[3]:
                    speech += "Reminder, '" + reminder[0] + "', from " + \
                              reminder[2] + " to " + reminder[-1] + ". "
                else:
                    speech += "Reminder, '" + reminder[0] + "', from " + \
                              reminder[2] + " to " + reminder[4] + ", " + \
                              reminder[5] + ", " + reminder[6] + ", " + \
                              reminder[7] + " at " + reminder[-1] + ". "
    if len(speech) == 0:
        speech = "You don't have reminders for the day."
    return speech


reminders = get_reminders()
reminders = classify_days(reminders)


@ask.launch
def launch():
    """
    Starts the skill.
    """
    speech_text = 'Welcome to Google Calendar. ' + \
                  'You can ask me to read all calendar or read reminders ' + \
                  'for a specific day'
    reprompt = "You can ask me to read all calendar or read reminders for " + \
               "a specific day. For example say 'reminders for today' or " + \
               "'reminders for Monday 24'."

    return question(speech_text).reprompt(reprompt)


@ask.intent('ReadGoogleCalendarIntent')
def read_google_calendar():
    """
    Alexa reads all reminders from Google Calendar
    """
    speech = all_calendar(reminders)
    speech += 'End of calendar... Goodbye.'
    return statement(speech)


@ask.intent('ReadSpecificDayIntent', convert={'day': 'date'})
def read_specific_day(day):
    """
    Alexa reads reminders for a specific day from Google Calendar
    """
    speech = specific_day(str(day), reminders)
    speech += "You can ask me for other day."
    return question(speech).reprompt("You can ask me for other day.")


@ask.intent('AMAZON.StopIntent')
def stop():
    return statement("Goodbye")


@ask.intent('AMAZON.CancelIntent')
def cancel():
    return statement("Goodbye")


@ask.session_ended
def session_ended():
    return "{}", 200


def _infodump(obj, indent=2):
    msg = json.dumps(obj, indent=indent)
    logger.info(msg)


if __name__ == '__main__':
    app.run(debug=True)
