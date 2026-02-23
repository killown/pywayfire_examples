#!/usr/bin/env python3
"""
Goal: Measures the 'Time to First Frame'.
Logic:
1. Subscribes to the compositor's 'view-mapped' event stream.
2. Launches the target application via STIPC.
3. Records the high-precision delta (perf_counter) once the first view appears.
"""

import sys
import time
import shutil
import os
import signal
from wayfire import WayfireSocket
from wayfire.extra.stipc import Stipc

if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} <app_command>")
    sys.exit(1)

app_cmd = sys.argv[1]

# Resolve full path if it's not an absolute or relative path
if not app_cmd.startswith(("/", "./", "../")):
    full_path = shutil.which(app_cmd)
    if full_path:
        app_cmd = full_path

sock = WayfireSocket()
stipc = Stipc(sock)

# Subscribe only to view-mapped events to catch the exact moment of rendering
sock.watch(["view-mapped"])

# Mark start time and execute
start_time = time.perf_counter()
stipc.run_cmd(app_cmd)

# PIDs may change during launch (forking/wrappers), so we stop at the first mapped view
while True:
    msg = sock.read_next_event()
    view = msg["view"]
    end_time = time.perf_counter()

    duration_ms = (end_time - start_time) * 1000
    msg_text = f"Startup Time: {duration_ms:.2f} ms"
    print(msg_text)

    pid = view.get("pid")
    if pid:
        os.kill(pid, signal.SIGTERM)

    break
