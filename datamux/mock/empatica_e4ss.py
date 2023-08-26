#!/usr/bin/env python3

"""
Mock E4 Streaming Server
Source: git@github.com:nirdslab/ee4ss_pretender.git

@author: Ben Mabe, Yasith Jayawardana

"""

import asyncio
import logging
import sys
from asyncio.streams import StreamReader, StreamWriter
from datetime import datetime
from threading import Thread
from typing import Dict

logger = logging.getLogger(__name__)
logger.level = logging.DEBUG
logger.addHandler(logging.StreamHandler(sys.stdout))


class Stream:
    def __init__(self, label: str, typ: str, freq: float, default_v: list):
        self.label = label
        self.typ = typ
        self.freq = freq or 0.1
        self.value = default_v
        self.last_t = 0.0
        self.last_v = None

    def read_latest(self):
        t = datetime.now().timestamp()
        if (t - self.last_t) > 1 / self.freq:
            self.last_t = t
            self.last_v = " ".join(map(str, self.value))
        return f"{self.label} {self.last_t} {self.last_v}"


STREAM_TYPES = ["acc", "bvp", "gsr", "ibi", "tmp", "bat", "tag", "hr"]
STREAMS: Dict[str, Stream] = {
    "acc": Stream("E4_Acc", "acc", 32, [100, 200, 300]),
    "bvp": Stream("E4_Bvp", "bvp", 64, [400]),
    "ibi": Stream("E4_Ibi", "ibi", 0, [500]),
    "gsr": Stream("E4_Gsr", "gsr", 4, [600]),
    "tmp": Stream("E4_Temperature", "tmp", 4, [700]),
    "hr": Stream("E4_Hr", "hr", 0, [800]),
    "bat": Stream("E4_Bat", "bat", 0, [1.0]),
    "tag": Stream("E4_Tag", "tag", 0, [1000]),
}


class SubscriptionContext:
    def __init__(self, r: StreamReader, w: StreamWriter) -> None:
        self.r = r
        self.w = w
        self.keepalive = True
        self.subscriptions = []
        self.paused = False
        self.ctx_thread = Thread(target=self.create_streaming_loop)
        self.ctx_thread.start()

    def subscribe(self, name: str):
        if name not in self.subscriptions:
            self.subscriptions.append(name)
        else:
            logger.warning(f"attempt to resubscribe to {name}")

    def unsubscribe(self, name: str):
        if name in self.subscriptions:
            self.subscriptions.remove(name)
        else:
            logger.warning(f"attempt to unsubscribe from non-subscribed {name}")

    def end(self):
        self.keepalive = False
        self.ctx_thread.join()

    async def __task__(self, stream_id: str):
        s = STREAMS[stream_id]
        while self.keepalive:
            if not self.paused and s.typ in self.subscriptions:
                data = s.read_latest()
                self.w.write(f"{data}\r\n".encode())
            await asyncio.sleep(1 / s.freq)

    def create_streaming_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tasks = []
        for stream_id in STREAMS:
            tasks.append(loop.create_task(self.__task__(stream_id)))
        loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))


def cmd_handler(msg: str, ctx: SubscriptionContext) -> str:
    # If msg does not exist, or cmd empty, return empty
    if not msg:
        return ""

    msg_parts = msg.split()
    cmd, args = msg_parts[0], msg_parts[1:]

    if cmd == "device_list":
        return "R device_list 2 | 9ff167 Empatica_E4 | 7a3166 Empatica_E4"

    if cmd == "device_connect":
        return "R device_connect OK"

    if cmd == "device_subscribe":
        if len(args) > 2:
            return "R device_subscribe ERR too many arguments"
        sub = args[0].lower()
        if sub in STREAM_TYPES:
            ctx.subscribe(sub)
            return f"R {cmd} {sub} OK"

    if cmd == "device_unsubscribe":
        if len(args) > 2:
            return "R device_unsubscribe ERR too many arguments"
        sub = args[0].lower()
        if sub in STREAM_TYPES:
            ctx.unsubscribe(sub)
            return f"R {cmd} {sub} OK"

    if cmd == "pause":
        if len(args) > 1:
            return "R pause ERR too many arguments"
        else:
            if args[0].upper() == "ON":
                if ctx.paused:
                    return "R pause ERR already paused"
                ctx.paused = True
                return "R pause ON"
            elif args[0].upper() == "OFF":
                if not ctx.paused:
                    return "R pause ERR not paused"
                ctx.paused = False
                return "R pause OFF"
            else:
                return "R pause ERR wrong argument"

    return ""


async def ee4_srv(r: StreamReader, w: StreamWriter):
    logger.info(f"connection established")
    # create new context for client
    ctx = SubscriptionContext(r, w)
    try:
        while not r.exception():
            msg_raw = await r.readline()
            msg = msg_raw.decode().strip()
            logger.info(f"< {msg}")
            out = cmd_handler(msg, ctx)
            logger.info(f"> {out}")
            w.write(f"{out}\r\n".encode())
            await w.drain()
    except UnicodeDecodeError:
        logger.warning("invalid char encountered")
    except AttributeError:
        logger.warning("attribute error encountered")
    except ConnectionError:
        logger.warning("connection error encountered")
    finally:
        logger.info("cleaning up resources")
        ctx.end()
    logger.info(f"resources purged. connection terminated.")


async def main():
    srv = await asyncio.start_server(ee4_srv, "localhost", 28000)
    host, port = srv.sockets[0].getsockname()
    logger.info(f"Streaming server started on {host}:{port}!")
    try:
        async with srv:
            await srv.serve_forever()
    except KeyboardInterrupt:
        await srv.wait_closed()
        exit(0)


if __name__ == "__main__":
    # In try-except to suppress irrelevant errors
    try:
        asyncio.run(main(), debug=True)
    except KeyboardInterrupt:
        exit(0)
