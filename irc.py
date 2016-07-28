#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket, logging
 
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
