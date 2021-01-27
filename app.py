#!/usr/bin/env python
import json, smtplib, configparser, argparse, os, re, socket
import datetime as dt
from argparse import ArgumentParser

config = configparser.ConfigParser()
config.read('config.ini')
MAIL_PORT = config['MAIL']['PORT']
MAIL_SERVER = config['MAIL']['SERVER']
USERNAME = config['MAIL']['USERNAME']
PSSWD = config['MAIL']['PSSWD']
SENDER = config['MAIL']['OUTGOING_MAIL']

DATEFORMAT, MAX_ATTEMPTS = '%Y-%m-%d', 3
bday_persons, bday, receiver_name, days = '', '', '', ''
msg_subject = "Subject: Birthday Reminder: {bday_persons}'s birthday on {bday}s"
msg_body = '''Hi {receiver_name},
This is a reminder that {bday_persons} will be celebrating their
birthday on {bday}.
There are {days} days left to prepare a present!
'''

def _get_employees_list(file_name):
    with open(file_name) as f:
        data = json.load(f)
    return data['employees'] if 'employees' in data else []

def days_left(birthday):
    bday = dt.datetime.strptime(birthday, DATEFORMAT).date()
    now = dt.datetime.now()
    bday_changed = dt.datetime(now.year, bday.month, bday.day)
    # +1 including today
    return (bday_changed - now.today()).days + 1

def _notify_congratulators(congratulators, celebrants_names, celebrants_date, up_to_days=7, attempts=1):
    try:
        with  smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT) as server:
            server.login(USERNAME, PSSWD)
            for congratulator in congratulators:
                subject = msg_subject.format(bday_persons=celebrants_names, bday=celebrants_date)
                body = msg_body.format(
                    receiver_name=congratulator['name'], bday_persons=celebrants_names, bday=celebrants_date, days=up_to_days)
                message = '{}\n\n{}'.format(subject, body)
                server.sendmail(SENDER, congratulator['email'], message)
        print('notifications sent')
    except socket.error:
        print("could not connect to {}:{}".format(MAIL_SERVER, MAIL_PORT))
        attempts = attempts + 1
        if attempts > MAX_ATTEMPTS:
            return
        _notify_congratulators(congratulators, celebrants_names, celebrants_date, up_to_days=up_to_days, attempts=attempts)

def _validate_file(f):
    if not os.path.exists(f):
        # Argparse uses the ArgumentTypeError to give a rejection message like:
        # error: argument input: x does not exist
        raise argparse.ArgumentTypeError("{0} does not exist".format(f))
    # https://www.geeksforgeeks.org/check-if-email-address-valid-or-not-in-python/
    mail_regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    valid_mail = lambda reg, mail: re.search(reg, mail)
    valid_date = lambda bday: dt.datetime.strptime(bday, DATEFORMAT)
    employees = _get_employees_list(f)
    try:
        for employee in employees:
            if not (employee['name'] and valid_mail(mail_regex, employee['email']) and valid_date(employee['birthday'])):
                raise argparse.ArgumentTypeError('Input file {} value do not meet constraints'.format(f))
    except (ValueError, KeyError):
         raise argparse.ArgumentTypeError('Input file {} value do not meet constraints'.format(f))
    return employees

def app(employees, up_to_days):
    celebrants = [employee for employee in employees if days_left(employee['birthday']) == up_to_days]
    if len(celebrants) > 0:
        congratulators = [e for e in employees if e not in celebrants]
        celebrants_names = ', '.join([celebrant['name'] for celebrant in celebrants])
        # 0 first celebrant
        celebrants_date = dt.datetime.strptime(celebrants[0]['birthday'], DATEFORMAT).strftime("%d %b")
        _notify_congratulators(congratulators, celebrants_names, celebrants_date, up_to_days)

if __name__ == "__main__":
    parser = ArgumentParser(description="Employee birthday notificator cli")
    parser.add_argument("file", type=_validate_file, help="json file")
    parser.add_argument("-d", "--days", help="up to days", type=int, default=19)
    args = parser.parse_args()
    app(args.file, args.days)