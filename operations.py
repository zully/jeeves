#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging, thread, time

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
    if split_line[1] == 'PRIVMSG' and 'hello' in msg:
        if '#' in split_line[2]:
            target = split_line[2]
        else:
            target = nick
        logging.info('LOG: Answered %s with "Hello!"' % nick)
        irc.command('PRIVMSG %s %s' % (target, 'Hello!'))
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
        time.sleep(60)
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
            thread.start_new_thread( threaded_timer, (irc, ' '.join(nicks), ) )
        except:
            logging.exception('LOG: Unable to start thread!')
    return
