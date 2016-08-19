# How to use: (based on https://doyle.ninja/scanning-single-word-twitter-names/ and https://gist.github.com/w4/6b177fc86340d5f5d8ae)
# install pip3 (since we are going to use python 3) with "sudo apt-get install python3-pip", then "sudo pip3 install pycurl stem", use any dictionary from https://github.com/first20hours/google-10000-english. Create an empty file named "found".
# download tor browser. (Or use the tor command line version, which can be installed following instructions https://www.torproject.org/docs/debian.html.en)
# If use tor browser, two ports 9150 and 9151 are used. If you use the command line version, change ports to 9050 and 9051 accordingly.
# open tor browser (or start tor command line tool with "tor", if 9050 port is occupied, use "pkill -9 tor" to kill the tor process and restart tor)
# "python3 twitter-scanner.py google-10000-english.txt found"

# Always this tool will not work because tor network is not stable

"""Twitter handle scanner

Scans a specified list for available twitter handles. When blocked by Twitter, the script
will automatically request another exitpoint from Tor and continue running until it runs
out of names.

Syntax:
    python3 twitter-scanner.py -h

Requires:
    curses
    stem (pip install stem)
    Tor (https://www.torproject.org/)
"""

import curses
import json
import os
import pycurl
import signal
import sys
from argparse import ArgumentParser, FileType
from io import BytesIO
from math import floor
from random import shuffle
from time import sleep

from stem import Signal
from stem.control import Controller

parser = ArgumentParser()
parser.add_argument('file', help='file to read names to scan from', type=FileType('r'))
parser.add_argument('log', help='file to log handle attempts to', type=FileType('r+'))
parser.add_argument('--port', help='tor socks proxy port', type=int, default=9150)
parser.add_argument('--control', help='tor control panel port', type=int, default=9151)
parser.add_argument('-p', '--password', help='tor control panel password', type=str)
parser.add_argument('-o', '--output', help='file to write handles to', type=FileType('a'))
args = parser.parse_args()

checked = []

if os.fstat(args.log.fileno()).st_size > 0:
    checked = json.load(args.log)


def signal_handler(signal, frame):
    """Handles SIGINT (ctrl-C) signals - clean application shutdown"""
    args.log.seek(0)
    json.dump(checked, args.log)
    curses.endwin()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def print_host_data(curl, screen):
    """Get some information about our current Tor node and print it out"""
    buffer = BytesIO()

    curl.setopt(pycurl.URL, 'http://wtfismyip.com/json')
    curl.setopt(pycurl.WRITEDATA, buffer)
    curl.perform()

    data = json.loads(buffer.getvalue().decode('UTF-8'))

    screen.addstr('\n'.join(['===================================',
                             'Node IP address: {0}'.format(data['YourFuckingIPAddress']),
                             'Node Location: {0}'.format(data['YourFuckingLocation']),
                             'Node Hostname: {0}'.format(data['YourFuckingHostname']),
                             'Node ISP: {0}'.format(data['YourFuckingISP']),
                             '===================================',
                             '']))


def request_new_route(curl):
    """Request a new Tor route and hopefully get a new exit node"""
    curl.close()

    with Controller.from_port(port=args.control) as controller:
        controller.authenticate(password=args.password)
        controller.signal(Signal.NEWNYM)


def new_curl_instance():
    """Create new curl handle due to us having to close the old one to get a new route"""
    curl = pycurl.Curl()
    curl.setopt(pycurl.PROXY, '127.0.0.1')
    curl.setopt(pycurl.PROXYPORT, args.port)
    curl.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5)

    return curl


names = [line.rstrip('\n') for line in args.file if line.rstrip('\n') not in checked]
shuffle(names)


def main(stdscr):
    # Work around to get colours to work in curses
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i, i, -1)

    curl = pycurl.Curl()
    curl.setopt(pycurl.PROXY, '127.0.0.1')
    curl.setopt(pycurl.PROXYPORT, args.port)
    curl.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5)

    y, x = stdscr.getmaxyx()

    curses.init_pair(1, curses.COLOR_BLACK, 1) # original value is 47, changed to 1 to stop reporting err
    stdscr.addstr("Twitter username scanner", curses.color_pair(1))
    stdscr.bkgd(' ', curses.color_pair(1))
    stdscr.refresh()

    window = stdscr.subwin(y - 2, x, 1, 0)
    curses.init_pair(2, curses.COLOR_WHITE, -1)

    window.bkgd(' ', curses.color_pair(2))
    window.scrollok(True)
    window.idlok(True)

    print_host_data(curl, window)

    amt = len(names)
    check = 0
    found = 0

    for name in names:
        stdscr.move(y - 1, 0)
        stdscr.addstr("{0}% |{1}{2}| {3}/{4} - we have found {5} available handles"
                      .format(round(check / amt * 100), '#' * floor(check / amt * 16),
                              ' ' * (16 - floor(check / amt * 16)), check, amt, found),
                      curses.color_pair(1))
        stdscr.refresh()

        window.refresh()
        buffer = BytesIO()

        curl.setopt(pycurl.URL,
                    'https://twitter.com/users/username_available?username={0}'.format(name))
        curl.setopt(pycurl.WRITEDATA, buffer)
        curl.perform()

        try:
            data = json.loads(buffer.getvalue().decode('UTF-8'))

            if data['valid']:
                window.addstr("{0} is available!\n".format(name), curses.color_pair(47))
                args.output.write('{0}\n'.format(name))
                found += 1
            else:
                window.addstr("{0} is not available - {1}\n".format(name, data['reason']),
                              curses.color_pair(9))
                checked.append(name)
        except json.JSONDecodeError:
            window.addstr("Twitter has blocked us. We're going to request another route\n",
                          curses.color_pair(28))
            args.log.seek(0)
            json.dump(checked, args.log)
            request_new_route(curl)
            sleep(10)
            curl = new_curl_instance()
            print_host_data(curl, window)

        check += 1


curses.wrapper(main)
