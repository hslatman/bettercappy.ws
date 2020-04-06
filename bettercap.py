import asyncio
import functools
import logging
import signal
import time

from bettercappy.agent import BetterCapAgent
from bettercappy.daemon import BetterCapDaemon

async def shutdown(signal, loop, daemon):
    """Cleanup tasks tied to the service's shutdown."""

    print("signal received. quitting ...")

    # cancel asyncio tasks
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks] # TODO: we might need some better cleanup for WebSocket tasks
    await asyncio.gather(*tasks, return_exceptions=True)

    # stop the Bettercap daemon
    daemon.stop()

    # end the loop
    loop.stop()


def main():

    print("starting bettercap daemon")
    daemon = BetterCapDaemon(binary="bin/bettercap", caplet="websocket.cap")
    daemon.start()

    agent = BetterCapAgent(username="username", password="password", interface="en0", tags_to_silence=[])
    time.sleep(1) # allow some time for the daemon to be initialized

    loop = asyncio.get_event_loop()

    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT, signal.SIGQUIT)
    for sig in signals:
        loop.add_signal_handler(
            sig, lambda sig=sig: asyncio.create_task(shutdown(sig, loop, daemon))
        )

    print("starting bettercap agent")
    loop.create_task(agent.start())
    loop.run_forever()


if __name__ == '__main__':
    # TODO: arguments / options
    main()

