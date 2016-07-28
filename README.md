# jeeves

jeeves is an IRC bot (under heavy early development) written in python.  A config.py, notify.list, and master.conf file are required.  Sample files are below:

### config.py
```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

## CONFIG FILE

channels = [ '#testing', '#mynewbot' ]
server = 'irc.network.org'
port = 6667
botnick = 'jeeves-srv'
ident = 'jeeves'
real_name = 'Channel and Notify bot'
home_dir = '/home/ircbot'
from_addy = 'notifier@example.com'
to_addy = '1234567890@txt.verizon.com'
```

### notify.list
```
# The following colon separated syntax can be used
# Note that no comments are allowed in the actual file
## nickname only
nick:
## nickname and ident
nick:ident
## nickname, ident, and any number of IP's or hostnames
nick:ident:example.com:192.168.:10.10.
## nickname, any ident, and any number of IP's or hostname
nick::example.com:192.168.:10.10.
```

### master.conf
```
# A single line with the master (owner's) information
## ident and any number of IP's or hostnames
ident:example.com:192.168.:10.10.
```
