#!/usr/bin/env python3

"""
main docstring...

to-do:
    - consider using [requests](http://docs.python-requests.org)

references:
    - 
    - https://connect.garmin.com/proxy/activity-service-1.3/
"""

import logging
import warnings
import os # mkdir, remove, utime, path.isdir, path.isfile
import time
from datetime import datetime
from getpass import getpass
import subprocess # to handle password managers
import urllib.request, urllib.error
import json

ch = logging.StreamHandler()
ch.setLevel(logging.WARNING) # adjust log level later with verbosity switch
ch.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
logging.captureWarnings(True)
log = logging.getLogger('gar')
log.setLevel(logging.DEBUG) # set the root logger level low
log.addHandler(ch)

def log_in(username, password):
    """

    """
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
    log.debug('built URL opener with cookie processor')

    log.debug('requesting single sign-on page from Garmin to establish session')
    q = urllib.request.Request('https://sso.garmin.com/sso/login')
    r = opener.open(q, timeout=100)
    log.debug('Garmin server response code: {}'.format(r.code))


    log.debug('attempting to log in as {} and get valid session ticket'.format(username))
    p = dict(username=username, password=password, embed='true')
    u = "https://sso.garmin.com/sso/login?service=https%3A%2F%2Fconnect.garmin.com%2Fmodern%2F&webhost=olaxpw-conctmodern000.garmin.com&source=https%3A%2F%2Fconnect.garmin.com%2Fen-US%2Fsignin&redirectAfterAccountLoginUrl=https%3A%2F%2Fconnect.garmin.com%2Fmodern%2F&redirectAfterAccountCreationUrl=https%3A%2F%2Fconnect.garmin.com%2Fmodern%2F&gauthHost=https%3A%2F%2Fsso.garmin.com%2Fsso&locale=en_US&id=gauth-widget&cssUrl=https%3A%2F%2Fstatic.garmincdn.com%2Fcom.garmin.connect%2Fui%2Fcss%2Fgauth-custom-v1.2-min.css&privacyStatementUrl=%2F%2Fconnect.garmin.com%2Fen-US%2Fprivacy%2F&clientId=GarminConnect&rememberMeShown=true&rememberMeChecked=false&createAccountShown=true&openCreateAccount=false&usernameShown=false&displayNameShown=false&consumeServiceTicket=false&initialFocus=true&embedWidget=false&generateExtraServiceTicket=false&globalOptInShown=true&globalOptInChecked=false&mobile=false&connectLegalTerms=true"
    #TODO# split the POST data out of the url^ so that this code is easier to read

    q = urllib.request.Request(url=u, data=urllib.parse.urlencode(p).encode('utf-8'))
    r = opener.open(q, timeout=100)
    # with open('/tmp/foo.html','wt') as f: f.write(r.read().decode('utf-8'))
    # At this point, the response page is different for FAILURE vs SUCCESS
    #TODO# Check the response and change the POST to see if login was successful.

    q = urllib.request.Request(url='https://connect.garmin.com/post-auth/login')
    r = opener.open(q, timeout=100)

    log.debug('logged in as {}'.format(username))
    return opener


def get_activity_list(opener):
    """

    """
    log.info('getting list of activities')
    start = 0
    u = 'http://connect.garmin.com/proxy/activity-search-service-1.0/json/activities?start={0}'
    q = urllib.request.Request(url=u.format(start))
    r = opener.open(q, timeout=100)
    j = json.loads(r.read())
    alist = [entry['activity'] for entry in j['results']['activities']]
    max_activities = int(j['results']['search']['totalFound'])
    #TODO# We'd rather just get the all the activity names at once...
    start += 20
    while start < max_activities:
        q = urllib.request.Request(url=u.format(start))
        log.debug('query: {}'.format(q.get_full_url()))
        r = opener.open(q, timeout=100)
        j = json.loads(r.read())
        alist.extend([entry['activity'] for entry in j['results']['activities']])
        start += 20
    log.info('found {0} activities'.format(len(alist)))
    return alist

def download(opener, activity, filetype='tcx', path='/tmp', retry=3):
    #TODO# try other than TCX
    msg = 'checking activity: {0}, {1}, ended {2}, uploaded {3}, device {4}'
    log.debug(msg.format(activity['activityId'],
                        activity['activityName']['value'],
                        activity['endTimestamp']['display'],
                        activity['uploadDate']['display'],
                        activity['device']['display'],
                    ))

    u = 'http://connect.garmin.com/proxy/download-service/export/{filetype}/activity/{id}?full=true'
    q = urllib.request.Request(url=u.format(filetype=filetype, id=activity['activityId']))
    filename = 'activity_{0}.{1}'.format(activity['activityId'],filetype)
    filepath = os.path.join(path,filename)

    if os.path.isfile(filepath):
        log.info('{0} already exists, skipping'.format(filepath))
        retry = 0
    elif activity['device']['display'] == 'Unknown':
        log.warn('activity {} appears to be manual entry, skipping'.format(activity['activityId']))
        retry = 0

    while retry > 0:
        log.info('downloading activity {}: {}'.format(
                activity['activityId'],
                activity['activityName']['value']))
        try:
            log.debug('query: {}'.format(q))
            r = opener.open(q, timeout=500)
            retry = 0
            with open(filepath,'w') as f:
                f.write(r.read().decode('utf-8'))
            log.debug('wrote {}'.format(filepath))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                log.warn('received HTTP 404 -- will retry')
                log.debug(q.get_full_url())
                time.sleep(7)
                retry -= 1
            elif e.code == 500 and filetype == 'tcx':
                log.warn('received HTTP 500 after attempting TCX download -- activity was probably uploaded as GPX')
                retry = 0
            elif e.code == 404 and filetype == 'fit': #TODO# handle separately from normal 404
                log.warn('received HTTP 404 after attempting FIT download -- activity was probably manually entered')
                retry = 0
            else:
                raise e


def set_timestamp_to_end(activity):
    log.info('setting activity timestamp to end')


def set_verbosity(verbosity):
    for h in log.handlers:
        if type(h) is logging.StreamHandler:
            h.setLevel(logging.ERROR - 10*verbosity)


def add_rotating_file_handler(logfile = 'gar.log'):
    import logging.handlers
    rfh = logging.handlers.RotatingFileHandler(logfile, maxBytes=2**20, backupCount=3)
    rfh.setLevel(logging.DEBUG)
    fmt = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    rfh.setFormatter(fmt)
    log.addHandler(rfh)


def main(username, passcmd="", endtimestamp=False, path = '/tmp',
        filetype='tcx', retry=3, max_activities=-1, verbosity=1, **kw):
    """
    Log in and download activities from Garmin Connect.

    """
    set_verbosity(verbosity)

    if passcmd:
        log.info('trying password as first line of output from: $ {}'.format(passcmd))
        p = subprocess.run(passcmd, shell=True, stdout=subprocess.PIPE)
        password = p.stdout.splitlines()[0].decode('utf-8')
    else:
        password = getpass()

    path = os.path.expanduser(path)
    if not os.path.isdir(path):
        log.debug('making target directory: {}'.format(path))
        os.mkdir(path)

    opener = log_in(username, password)

    for activity in get_activity_list(opener): #TODO# optionally limited range
        download(opener, activity, filetype, path, retry)
        if endtimestamp:
            set_timestamp_to_end(activity)



if __name__ == "__main__":
    # use argparse to handle command-line arguments
    import argparse

    # instatiate parser
    parser = argparse.ArgumentParser(
            description='Garmin Connect activity archiver',
            prefix_chars='-'
            )
    parser.add_argument('-V', '--version', action='version',
            version='%(prog)s 0.0.1',
            help='display version information and exit')
    parser.add_argument('username', type=str,
            help='username to use when logging into Garmin Connect')
    parser.add_argument('-v','--verbosity', action='count', default=1,
            help='display verbose output')
    parser.add_argument('-P','--passcmd', type=str,
            help='command to get password for logging into Garmin Connect')
    parser.add_argument('-e','--endtimestamp', action='store_true', default=False,
            help='set downloaded file timestamps to activity end')
    parser.add_argument('-p', '--path', type=str,
            help='root path to download into')

    # actually parse the arguments
    args = parser.parse_args()

    # add a logging file if you are running from the command line
    add_rotating_file_handler()

    # call the main method to do something interesting
    main(**args.__dict__) #TODO more pythonic?