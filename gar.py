#!/usr/bin/env python3

"""
main docstring...

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
import io
import zipfile

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


def get_activity_list_page(opener, page=1, limit=100):
    """

    """
    u = 'http://connect.garmin.com/proxy/activity-search-service-1.0/json/activities?limit={limit}&currentPage={page}'
    q = urllib.request.Request(url=u.format(limit=limit, page=page))
    log.debug('query: {}'.format(q.get_full_url()))
    r = opener.open(q, timeout=100)
    j = json.loads(r.read().decode('utf-8'))
    #TODO# decode not needed in py3.6.2, but needed in py3.4.0
    activities = [entry['activity'] for entry in j['results']['activities']]

    total_pages = int(j['results']['search']['totalPages'])
    log.debug('retrieved page {0} of {1}'.format(page, total_pages))

    return activities, total_pages


def get_activity_list(opener, max_activities=-1):
    """

    """
    log.info('getting list of activities')

    page = 1
    if max_activities < 0 or max_activities > 100:
        limit = 100
    else: # 0 < max_activities < 100
        limit = max_activities
    activities, total_pages = get_activity_list_page(opener, page, limit)

    while page < total_pages and len(activities) < max_activities:
        page += 1
        a, _tp = get_activity_list_page(opener, page, limit)
        activities.extend(a)

    log.info('found {0} activities'.format(len(activities)))
    return activities


def download(opener, activity, ext='tcx', path='/tmp', retry=3):
    msg = 'checking activity: {0}, {5}, {1}, ended {2}, uploaded {3}, device {4}'
    log.debug(msg.format(activity['activityId'],
                        activity['activityName']['value'],
                        activity['endTimestamp']['display'],
                        activity['uploadDate']['display'],
                        activity['device']['display'],
                        ext
                    ))

    sub = dict(tcx = 'export/tcx', fit = 'files')
    u = 'https://connect.garmin.com/modern/proxy/download-service/{sub}/activity/{id}'
    q = urllib.request.Request(url=u.format(sub=sub[ext], id=activity['activityId']))
    filename = 'activity_{0}.{1}'.format(activity['activityId'],ext)
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
            log.debug('query: {}'.format(q.get_full_url()))
            r = opener.open(q, timeout=500)
            retry = 0
            if ext == "tcx":
                with open(filepath,'wt') as f:
                    f.write(r.read().decode('utf-8'))
            else: # ext == "fit":
                afn = '{}.fit'.format(activity['activityId'])
                zf = zipfile.ZipFile(io.BytesIO(r.read()))
                try:
                    info = zf.getinfo(afn)
                except KeyError:
                    log.warn('did not find {} in zip archive'.format(afn))
                    retry = 0
                else:
                    log.info('unzipped {x.filename} is {x.file_size} bytes, last modified {x.date_time}'.format(x=info))
                    with open(filepath,'wb') as f:
                        f.write(zf.read(afn))
            log.debug('wrote {}'.format(filepath))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                log.warn('received HTTP 404 -- will retry')
                time.sleep(7)
                retry -= 1
            elif e.code == 500 and ext == 'tcx':
                log.warn('received HTTP 500 after attempting TCX download -- activity was probably uploaded as GPX')
                retry = 0
            elif e.code == 404 and ext == 'fit': #TODO# handle separately from normal 404
                log.warn('received HTTP 404 after attempting FIT download -- activity was probably manually entered')
                retry = 0
            else:
                raise e


def set_timestamp_to_end(activity, ext='tcx', path='/tmp'):
    fn = 'activity_{0}.{1}'.format(activity['activityId'],ext)
    fp = os.path.join(path,fn)
    ets = activity['endTimestamp']
    log.info('setting {0} timestamp to {1}'.format(fp, ets['display']))
    try:
        os.utime(fp, (datetime.now().timestamp(), int(ets['millis'])/1000))
    except FileNotFoundError:
        log.warn('could not find {0} to set timestamp, skipping'.format(fp))


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


def main(username, passcmd="", endtimestamp=True, path = '/tmp',
        tcx=False, fit=False, retry=3, max_activities=-1, verbosity=1, **kw):
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

    for activity in get_activity_list(opener, max_activities):
        if fit:
            download(opener, activity, 'fit', path, retry)
        if tcx:
            download(opener, activity, 'tcx', path, retry)
        if endtimestamp:
            if tcx:
                set_timestamp_to_end(activity, 'tcx', path)
            if fit:
                set_timestamp_to_end(activity, 'fit', path)



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
    parser.add_argument('-n','--max-activities', type=int, default=-1,
            help='display verbose output')
    parser.add_argument('-P','--passcmd', type=str,
            help='command to get password for logging into Garmin Connect')
    parser.add_argument('-e','--endtimestamp', action='store_true', default=True,
            help='set downloaded file timestamps to activity end')
    parser.add_argument('-p', '--path', type=str, default='./activities',
            help='root path to download into')
    parser.add_argument('-t', '--tcx', action='store_true', default=False,
            help='download exported .tcx files')
    parser.add_argument('-f', '--fit', action='store_true', default=False,
            help='download (original) .fit files')

    # actually parse the arguments
    args = parser.parse_args()

    # add a logging file if you are running from the command line
    add_rotating_file_handler(os.path.join(args.path, 'gar.log'))

    # call the main method to do something interesting
    main(**args.__dict__) #TODO more pythonic?
