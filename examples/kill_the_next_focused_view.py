import os
import signal
from wayfire import WayfireSocket

sock = WayfireSocket()
sock.watch()

while True:
    if (pid := (msg := sock.read_message()).get("view", {}).get("pid")) and msg.get("event") == 'view-focused':
        os.kill(pid, signal.SIGTERM)
        break
