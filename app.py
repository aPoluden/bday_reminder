import json, smtplib, configparser, argparse, os
import datetime as dt
from argparse import ArgumentParser

config = configparser.ConfigParser()
config.read('config.ini')
MAIL_PORT = config['MAIL']['PORT']
MAIL_SERVER = config['MAIL']['SERVER']
USERNAME = config['MAIL']['USERNAME']
PSSWD = config['MAIL']['PSSWD']
SENDER = config['MAIL']['OUTGOING_MAIL']

bday_persons, bday, receiver_name, days = '', '', '', ''
msg_subject = "Subject: Birthday Reminder: {bday_persons}'s birthday on {bday}s"
msg_body = '''Hi {receiver_name},
This is a reminder that {bday_persons} will be celebrating their
birthday on {bday}.
There are {days} days left to prepare a present!
'''

def get_employees_list(file_name):
    with open(file_name) as f:
        data = json.load(f)
    return data['employees'] if 'employees' in data else []

def days_left(birthday):
    bday = dt.datetime.strptime(birthday, '%Y-%m-%d').date()
    now = dt.datetime.now()
    bday_changed = dt.datetime(now.year, bday.month, bday.day)
    # +1 including today
    return (bday_changed - now.today()).days + 1

def _notify_congratulators(congratulators, celebrants_names, celebrants_date, up_to_days=7):
    server = smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT)
    server.login(USERNAME, PSSWD)
    for congratulator in congratulators:
        subject = msg_subject.format(bday_persons=celebrants_names, bday=celebrants_date)
        body = msg_body.format(
            receiver_name=congratulator['name'], bday_persons=celebrants_names, bday=celebrants_date, days=up_to_days)
        message = '{}\n\n{}'.format(subject, body)
        server.sendmail(SENDER, congratulator['email'], message)
    server.quit()

def notify(employees, up_to_days):
    celebrants = [employee for employee in employees if days_left(employee['birthday']) == up_to_days]
    if len(celebrants) > 0:
        congratulators = [e for e in employees if e not in celebrants]
        celebrants_names = ', '.join([celebrant['name'] for celebrant in celebrants])
        celebrants_date = dt.datetime.strptime(celebrants[0]['birthday'], '%Y-%m-%d').strftime("%d %b")
        _notify_congratulators(congratulators, celebrants_names, celebrants_date, up_to_days)

def validate_file(f):
    if not os.path.exists(f):
        # Argparse uses the ArgumentTypeError to give a rejection message like:
        # error: argument input: x does not exist
        raise argparse.ArgumentTypeError("{0} does not exist".format(f))
    return f

if __name__ == "__main__":
    parser = ArgumentParser(description="Employee birthday notificator cli")
    parser.add_argument("file", type=validate_file, help="json file")
    parser.add_argument("-d", "--days", help="up to days", type=int, default=7)
    parser.add_argument("-v", "--validate", help="validate the data file", action="store_true")
    # TODO implement logic