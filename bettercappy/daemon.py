import os
import signal
import subprocess

class BetterCapDaemon(object):

    def __init__(self, binary='bin/bettercap', caplet='some.cap'):
        self._cmd = [binary, '-no-colors', '-caplet', caplet]
        self._process = None

    def preexec_function(self):
        # Prevent the SIGINT signal from arriving to the subprocess by ignoring it.
        # Solution based on https://stackoverflow.com/questions/5045771/python-how-to-prevent-subprocesses-from-receiving-ctrl-c-control-c-sigint
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        # This probably does not work for Windows; we might need creationflags for that; something like:
        #import sys
        #if sys.platform.startswith('win'):
        #    creationflags=0x00000200
        # And add the creationflags as parameter to the subprocess.Popen.
        # 
        # Another option that might work (but didn't in my test), is to use the following:
        #os.setpgrp(); os.setpgrp(0, 0)

    def start(self):
        if self._process:
            return

        p = subprocess.Popen(self._cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=self.preexec_function)
        self._process = p

    def stop(self):
        if not self._process:
            return

        self._process.terminate()
        self._process.wait(10.0)