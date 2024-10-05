import os
import signal
from wayfire import WayfireSocket

sock = WayfireSocket()
sock.watch()

while True:
    msg = sock.read_message()
    if "event" in msg:
        if 'view-focused' in msg['event']:
            pid = msg['view']['pid']
            print(f"Killing process with PID: {pid}")
            os.kill(pid, signal.SIGTERM)
            break
