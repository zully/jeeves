#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging, sys, smtplib, os.path

# open a file and return contents
def open_file(filename):
    if os.path.isfile(filename):
        try:
            f = open(filename, 'r')
        except IOError as e:
            logging.exception('LOG: I/O error({0}): {1}'.format(e.errno, e.strerror))
            sys.exit(1)
        except: # Handle other exceptions such as attribute errors
            logging.exception('LOG: Unexpected error: ', sys.exc_info()[0])
            sys.exit(1)
    else:
        logging.error('LOG: %s: File not found!' % notify_list)
        sys.exit(1)
    return f

# read the notify list
def read_notifylist(notify_list):
    f = open_file(notify_list)
    nicks = {}
    for line in f:
        working_array=line.rstrip('\n').split(':')
        working_array.insert(1, 0)
        nicks[working_array[0]] = working_array[1:]
    if f is not None:
        f.close()
    logging.info('LOG: Notifying on: %s' % ', '.join(nicks.keys()))
    return nicks

# read master file
def read_master(master_file):
    f = open_file(master_file)
    master = []
    for line in f:
        master=line.rstrip('\n').split(':')
    if f is not None:
        f.close()
    return master

# Send message to user that a friend is on IRC
def send_message(from_addy, to_addy, message):
    try:
        smtpObj = smtplib.SMTP('localhost')
        smtpObj.sendmail(to_addy, from_addy, message)
    except:
        logging.exception('LOG: Unexpected error: ', sys.exc_info()[0])
    return

# process data for notification agent
def get_masks(irc, ison, nicks):
    should_execute = False
    # pop off the object before nicks
    for i in xrange(3):
        ison.pop(0)
    # if the nicklist is empty, pop off the last object
    if ison[0] == ':':
        ison.pop(0)
    # otherwise strip the : of the first nick
    else:
        ison[0] = ison[0].lstrip(':')
    # if the nicklist is not empty
    if len(ison) > 0:
        # for each item in the nicklist, make the nick lowercase
        for i in range(len(ison)):
            ison[i] = ison[i].lower()
        for n in ison:
            if nicks[n][0] == 0:
                should_execute = True
                nicks[n][0] = 1
        if should_execute:
            irc.command('WHO %s' % ','.join(ison))
    for n in nicks.keys():
        if nicks[n][0] == 2 or nicks[n][0] == 3:
            if n not in ison:
                if nicks[n][0] == 2:
                    logging.info('LOG: %s has left IRC.' % n)
                if nicks[n][0] == 3:
                    logging.info('LOG: %s (UNKNOWN) has left IRC.' % n)
                nicks[n][0] = 0
    return nicks

# run a few more checks and notify the user if passed
def notify_user(to_addy, from_addy, split_line, nicks):
    ident = split_line[4]
    ip = split_line[5]
    nick = split_line[7].lower()
    name = split_line[10]
    if nicks[nick][0] == 1:
        if nicks[nick][1] in ident or nicks[nick][1] == '':
            if len(nicks[nick]) > 2:
                for nip in nicks[nick][2:]:
                    if nip in ip:
                        message = ' %s is on IRC.\n%s\n%s\n[%s]' % (nick, ident, ip, name)
                        send_message(to_addy, from_addy, message)
                        logging.info('LOG: %s %s@%s [%s] is on IRC.' % (nick, ident, ip, name))
                        nicks[nick][0] = 2
            else:
                message = ' %s is on IRC.\n%s\n%s\n[%s]' % (nick, ident, ip, name)
                send_message(to_addy, from_addy, message)
                logging.info('LOG: %s %s@%s [%s] is on IRC.' % (nick, ident, ip, name))
                nicks[nick][0] = 2
    if nicks[nick][0] == 1:
        logging.info('LOG: %s %s@%s [%s] does not match criteria!' % (nick, ident, ip, name)) 
        logging.info('LOG: Setting %s as UNKNOWN (Level: 3)' % nick)
        nicks[nick][0] = 3
    return nicks
