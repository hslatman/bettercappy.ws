import logging
import requests
import subprocess
import threading
import time
import websockets

from requests.auth import HTTPBasicAuth

class BetterCapClient(object):
    def __init__(self, hostname='localhost', scheme='http', port=8901, username=None, password=None):
        # NOTE: the BetterCapClient is based on code in https://github.com/evilsocket/pwnagotchi/blob/master/pwnagotchi/bettercap.py
        # We've taken bits and pieces required for establishing a connection to Bettercap and left out pwnagotchi specific parts
        self._hostname = hostname
        self._scheme = scheme
        self._port = port
        self._username = username
        self._password = password
        self._url = "%s://%s:%d/api" % (scheme, hostname, port)
        self._auth = HTTPBasicAuth(username, password)

    def _decode(self, r, verbose_errors=True):
        try:
            return r.json()
        except Exception as e:
            if r.status_code == 200:
                logging.error("error while decoding json: error='%s' resp='%s'" % (e, r.text))
            else:
                err = "error %d: %s" % (r.status_code, r.text.strip())
                if verbose_errors:
                    logging.info(err)
                raise Exception(err)
            return r.text

    def session(self):
        r = requests.get("%s/session" % self._url, auth=self._auth)
        return self._decode(r)

    def events(self):
        r = requests.get("%s/events" % self._url, auth=self._auth)
        return self._decode(r)

    def run(self, command, verbose_errors=True):
        r = requests.post("%s/session" % self._url, auth=self._auth, json={'cmd': command})
        return self._decode(r, verbose_errors=verbose_errors)


class BetterCapAgent(BetterCapClient):
    def __init__(self, hostname='localhost', scheme='http', port=8901, username=None, password=None, interface=None, tags_to_silence=[]):
        # NOTE: the BetterCapAgent is based on code in https://github.com/evilsocket/pwnagotchi/blob/master/pwnagotchi/agent.py
        # We've taken bits and pieces required for establishing a connection to Bettercap and left out pwnagotchi specific parts
        super(BetterCapAgent, self).__init__(hostname=hostname, scheme=scheme, port=port, username=username, password=password)
        self._interface = interface
        self._tags_to_silence = tags_to_silence

    def start_module(self, module):
        self.run('%s on' % module)

    def restart_module(self, module):
        self.run('%s off; %s on' % (module, module))

    def is_module_running(self, module):
        s = self.session()
        for m in s['modules']:
            if m['name'] == module:
                return m['running']
        return False

    def setup_events(self):
        for tag in self._tags_to_silence:
            try:
                self.run(f"events.ignore {tag}", verbose_errors=False)
            except Exception as e:
                logging.error(f"error occurred in setup_events: {e}")

    def start_monitor_mode(self):

        restart = False
        has_mon = False

        while has_mon is False:
            s = self.session()
            for iface in s['interfaces']:
                if iface['name'] == self._interface:
                    logging.info(f"found monitor interface: {iface['name']}")
                    has_mon = True
                    break

            if has_mon is False:
                logging.info(f"waiting for monitor interface {self._interface} ...")
                time.sleep(1)

        net_recon_running = self.is_module_running('net.recon')
        net_probe_running = self.is_module_running('net.probe')

        if net_recon_running and restart:
            self.restart_module('net.recon')
            self.run('net.clear')
        elif not net_recon_running:
            self.start_module('net.recon')

        if net_probe_running and restart:
            self.restart_module('net.probe')
            self.run('net.clear')
        elif not net_probe_running:
            self.start_module('net.probe')


    async def consumer(self, message):
        logging.info(message) # NOTE: we can do something (more) usefull with the information 

    async def consumer_handler(self, websocket, path):
        # TODO: exception handling when handling messages
        async for message in websocket:
            await self.consumer(message)

    async def start_websocket(self):

        # TODO: exception handling during connection setup
        uri = f"ws://{self._username}:{self._password}@{self._hostname}:{self._port}/api/events"
        async with websockets.connect(uri) as websocket:
            logging.info(f"websocket connection established to {websocket.host}:{websocket.port}")
            await self.consumer_handler(websocket, 'bla')


    async def start(self):
        self.setup_events()
        self.start_monitor_mode()
        await self.start_websocket() 


    # TODO: a stop method?
