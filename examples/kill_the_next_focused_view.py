import os
import signal
import subprocess
from wayfire import WayfireSocket

def kill_process(identifier):
    try:
        # If the identifier is an integer (PID), terminate the process by PID
        if isinstance(identifier, int):
            os.kill(identifier, signal.SIGTERM)
        else:
            # If the identifier is a string (app-id), terminate the process by name
            subprocess.run(["pkill", identifier])
    except Exception as e:
        print(f"Failed to kill process: {e}")

sock = WayfireSocket()
sock.watch()

while True:
    msg = sock.read_message()
    app_id = msg.get('view', {}).get('app-id')
    pid = msg.get('view', {}).get('pid')

    # Attempt to kill the process by PID
    kill_process(pid)

    # Attempt to kill the process by application ID (name)
    # This is important for applications like Steam, which may not allow
    # termination by PID alone due to being launched in a manner that 
    # creates child processes. Using the app-id ensures that all instances 
    # of the application can be terminated effectively, even if the PID 
    # reference is stale or if the application manages multiple processes.
    kill_process(app_id)

    break

