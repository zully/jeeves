#!/usr/bin/env python
# -*- coding: utf-8 -*-

from irc import *
from operations import *
from notify import *
from time import sleep
import config, signal

def main():
    # Set up logging
    set_up_logs(config.home_dir, config.botnick)

    # read configs
    nicks = read_notifylist(config.home_dir + 'notify.list')
    master = read_master(config.home_dir + 'master.conf')
    
    # configure IRC object and connect
    irc = IRC()
    irc.connect(config.server, config.port, config.botnick, config.ident, config.real_name)

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
                elif action == 'JOIN' or action == 'PART' or action == 'PRIVMSG':
                    perform_op(irc, split_line, config.botnick, master)
                # execute on who return for notifier
                elif action == '352':
                    nicks = notify_user(config.to_addy, config.from_addy, split_line, nicks)
                # respond to server PING
                elif line.find('PING :') != -1:
                    send_pong(irc, line)
                # initiate startup sequence once connected
                elif action == '255':
                    start_up(irc, config.channels, nicks.keys(), config.server)
                # wait and then reconnect on disconnect
                elif line.find('ERROR :Closing Link') != -1 or line.find('ERROR :Your host is trying to (re)connect too fast') != -1:
                    logging.info('LOG: Waiting 120 seconds before attempting reconnect.')
                    sleep(120)
                    irc.connect(config.server, config.port, config.botnick, config.ident, config.real_name)
        except KeyboardInterrupt:
            irc.command('QUIT Goodbye.')
            logging.info('LOG: Goodbye.')
            sys.exit(0)
        except: # Handle other exceptions such as attribute errors
            logging.exception('LOG: Unexpected error: ', sys.exc_info()[0])
            sys.exit(1)
    return

signal.signal(signal.SIGTERM, signal_handler)

if __name__ == '__main__':
    main()
