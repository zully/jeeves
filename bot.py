#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, socket, logging, thread, time, signal, smtplib, config # noqa

CONNECTING = False


class IRC:

    irc = socket.socket()

    def __init__(self):
        self.irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return

    def command(self, command):
        self.irc.send('%s\r\n' % command)
        return

    def connect(self, server, port, botnick, ident, real_name):
        logging.info('LOG: Connecting to %s' % server)
        self.irc.connect((server, port))
        self.irc.send('NICK %s\r\n' % botnick)
        self.irc.send('USER %s 0 * :%s\r\n' % (ident, real_name))
        return

    def get_text(self):
        raw_data = self.irc.recv(2040)
        split_data = raw_data.split('\n')
        lines = []
        for line in split_data:
            if len(line) > 0:
                lines.append(line.rstrip('\r').lstrip(':'))
        return lines


# open a file and return contents
def open_file(filename):
    if os.path.isfile(filename):
        try:
            f = open(filename, 'r')
        except IOError as e:
            logging.exception('LOG: I/O error({0}): {1}'.format(e.errno,
                                                                e.strerror))
            sys.exit(1)
        except:  # Handle other exceptions such as attribute errors
            logging.exception('LOG: Unexpected error: ', sys.exc_info()[0])
            sys.exit(1)
    else:
        logging.error('LOG: %s: File not found!' % filename)
        sys.exit(1)
    return f


# read the notify list
def read_notifylist(notify_list):
    f = open_file(notify_list)
    nicks = {}
    for line in f:
        working_array = line.rstrip('\n').split(':')
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
        master = line.rstrip('\n').split(':')
    if f is not None:
        f.close()
    return master


# Send message to user that a friend is on IRC
def send_message(from_addy, to_addy, message):
    try:
        smtpObj = smtplib.SMTP('localhost')
        smtpObj.sendmail(to_addy, from_addy, message)
        logging.info('LOG: Message sent! MSG: %s' % message)
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
                        message = ' %s is on IRC.\n%s\n%s\n[%s]' % (nick,
                                                                    ident,
                                                                    ip,
                                                                    name)
                        send_message(to_addy, from_addy, message)
                        logging.info('LOG: %s %s@%s [%s] is on IRC.' % (nick,
                                                                        ident,
                                                                        ip,
                                                                        name))
                        nicks[nick][0] = 2
            else:
                message = ' %s is on IRC.\n%s\n%s\n[%s]' % (nick, ident,
                                                            ip, name)
                send_message(to_addy, from_addy, message)
                logging.info('LOG: %s %s@%s [%s] is on IRC.' % (nick, ident,
                                                                ip, name))
                nicks[nick][0] = 2
    if nicks[nick][0] == 1:
        logging.info('LOG: %s %s@%s [%s] does not match criteria!' % (nick,
                                                                      ident,
                                                                      ip,
                                                                      name))
        logging.info('LOG: Setting %s as UNKNOWN (Level: 3)' % nick)
        nicks[nick][0] = 3
    return nicks


def set_up_logs(home_dir, botnick):
    # Configure logging
    logging.basicConfig(filename=('%s%s.log' % (home_dir, botnick.lower())),
                        format='%(asctime)s %(message)s',
                        datefmt='%b %d %H:%M:%S',
                        level=logging.DEBUG)
    return


def signal_handler(signum, frame):
    if signum == 15:
        raise KeyboardInterrupt('Exit Gracefully')
    return


# perform the operation indicated
def perform_op(irc, split_line, botnick, master):
    tmp = split_line[0].split('!', 1)
    nick = tmp[0]
    tmp = tmp[1].split('@', 1)
    ident = tmp[0]
    ip = tmp[1]

    if split_line[1] == 'PRIVMSG':
        msg = ' '.join(split_line[3:]).lstrip(':')
        if '#' in split_line[2]:
            logging.info('CHAN: %s %s: %s' % (split_line[2], nick, msg))
        else:
            logging.info('PRIV: %s: %s' % (nick, msg))
    elif split_line[1] == 'JOIN':
        if botnick != nick:
            if master[0] in ident:
                for nip in master[1:]:
                    if nip in ip:
                        logging.info('LOG: Performed OP (+o) on %s' % nick)
                        irc.command('MODE %s +o %s' % (split_line[2], nick))
    elif split_line[1] == 'PRIVMSG' and '.whois' in msg:
        logging.info('LOG: Performed WHOIS on %s' % nick)
        irc.command('WHOIS %s' % nick)

    return


# timer function
def threaded_timer(irc, nicks):
    while True:
        irc.command('ISON %s' % nicks)
        time.sleep(150)
    return


def connection_test_timer(irc):
    logging.info("connection test timer started")
    time.sleep(30)
    global CONNECTING
    if CONNECTING:
        logging.info("still waiting for connection, restarting")
        irc.connect(config.server, config.port, config.botnick,
                    config.ident, config.real_name)
        CONNECTING = True
    return


# send pong response to server
def send_pong(irc, line):
    response = 'PONG %s\r\n' % line.split()[1]
    irc.command(response)
    logging.info('RAW: %s' % response.rstrip())
    return


# Do start up sequence and start separate timer thread
def start_up(irc, channels, nicks, server):
    logging.info('LOG: Connected to %s!' % server)
    if len(channels) > 0:
        for channel in channels:
            irc.command('JOIN %s' % channel)
        try:
            thread.start_new_thread(threaded_timer, (irc, ' '.join(nicks), ))
        except:
            logging.exception('LOG: Unable to start thread!')
    return


# Set up logging
set_up_logs(config.home_dir, config.botnick)


def main():

    # read configs
    nicks = read_notifylist(config.home_dir + 'notify.list')
    master = read_master(config.home_dir + 'master.conf')

    # configure IRC object and connect
    irc = IRC()
    irc.connect(config.server, config.port, config.botnick,
                config.ident, config.real_name)
    global CONNECTING
    CONNECTING = True
    try:
        thread.start_new_thread(connection_test_timer, irc)
    except:
        logging.exception('LOG: Unable to start thread!')

    while True:
        try:
            # Read in new data and log them
            lines = irc.get_text()
            for line in lines:
                logging.info('RAW: %s' % line)
                split_line = line.split()
                action = split_line[1]

                # execute on ISOP return for notifier
                if action == '303':
                    nicks = get_masks(irc, split_line, nicks)
                # execute on JOIN/PART or PRIVMSG
                elif action == 'JOIN' or action == 'PART' or action == 'PRIVMSG': # noqa
                    perform_op(irc, split_line, config.botnick, master)
                # execute on who return for notifier
                elif action == '352':
                    nicks = notify_user(config.to_addy, config.from_addy,
                                        split_line, nicks)
                # respond to server PING
                elif line.find('PING :') != -1:
                    send_pong(irc, line)
                # initiate startup sequence once connected
                elif action == '255':
                    start_up(irc, config.channels, nicks.keys(), config.server)
                    CONNECTING = False

                # wait and then reconnect on disconnect
                elif line.find('ERROR :Closing Link') != -1 or line.find('ERROR :Your host is trying to (re)connect too fast') != -1: # noqa
                    logging.info('LOG: Waiting 120 seconds before attempting reconnect...') # noqa
                    time.sleep(120)
                    logging.info('LOG: Attempting re-connect...')
                    irc.connect(config.server, config.port, config.botnick,
                                config.ident, config.real_name)
                    CONNECTING = True
                    try:
                        thread.start_new_thread(connection_test_timer, irc)
                    except:
                        logging.exception('LOG: Unable to start thread!')

        except KeyboardInterrupt:
            irc.command('QUIT Goodbye.')
            logging.info('LOG: Goodbye.')
            sys.exit(0)
        except:  # Handle other exceptions such as attribute errors
            logging.exception('LOG: Unexpected error: ', sys.exc_info()[0])
            sys.exit(1)
    return


signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGHUP, signal_handler)

if __name__ == '__main__':
    main()
