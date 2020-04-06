# bettercappy.ws

A small POC of running bettercap with WebSockets instead of polling the REST API

## Description

This repository contains a minimal POC for running bettercap as a daemon and 
subscribing to it using a WebSocket connection. The daemon is wrapped by a 
small Python script. The WebSocket connection is established by a custom
bettercap Agent, the implementation of which has been based on the one as 
found in [pwnagotchi](https://github.com/evilsocket/pwnagotchi/blob/master/pwnagotchi/agent.py) to
get up and running fast.

## Caveats

Please note that this repository does not (yet) contain a description of how to make
the bettercap [web ui](https://github.com/bettercap/ui) work with WebSockets. By enabling WebSocket support, the default
events API is disabled, resulting in an empty event log in the Web UI.

## TODOs

TODOs are scattered around in the codebase.