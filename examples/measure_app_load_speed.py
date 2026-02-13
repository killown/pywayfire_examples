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
from wayfire import WayfireSocket
from wayfire.extra.stipc import Stipc

if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} <app_command>")
    sys.exit(1)

app_cmd = sys.argv[1]

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
    print(f"Startup Time: {duration_ms:.2f} ms")
    print(f"View Info: {view.get('app-id')} - {view.get('title')}")
    break
