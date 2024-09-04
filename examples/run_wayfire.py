import os
from wayfire import WayfireSocket
from wayfire.extra.ipc_utils import WayfireUtils
from subprocess import Popen
from uuid import uuid4
from time import sleep
from datetime import datetime, timezone
from random import uniform

socket = WayfireSocket()
utils = WayfireUtils(socket)

def run_wayfire(wayfire_path: str, logfile: str, cfgfile: str):
    """
    Start a Wayfire instance with a IPC connection.

    Args:
        wayfire_path (str): Path to the Wayfire executable.
        logfile (str): Path to the file where logs will be written.
        cfgfile (str): Path to the configuration file for Wayfire.

    Returns:
        A tuple containing: The Wayfire process, Display Name and IPC socket.

    Example: process, display, socket = run_wayfire("/usr/bin/wayfire",
                                                    "/path/to/wayfire.log",
                                                    "/path/to/wayfire.ini")

    Raises:
        Exception: If unable to connect to the Wayfire IPC socket.
    """
    id = str(uuid4())
    socket_name = f"/tmp/wayfire-{id}.socket"

    env = os.environ.copy()
    env['_WAYFIRE_SOCKET'] = socket_name

    def get_now():
       return datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

    def get_display_name_from_log():
        with open(logfile, "r") as log:
            for line in log:
                if "Using socket name" in line:
                    parts = line.split("Using socket name")
                    if len(parts) > 1:
                        display_name = parts[1].strip()
                        return display_name
            return None

    with open(logfile, "w") as log:
        log.write(f'Wayfire instance starting at {get_now()}\n')
        log.flush()

        # Run Wayfire with the generated socket name for IPC communication
        wayfire_process = Popen(
            [wayfire_path, '-c', cfgfile],
            stdout=log, stderr=log, env=env, preexec_fn=os.setsid
        )

        sleep(1.5 + uniform(0, 1))

        socket = WayfireSocket(socket_name)
        display = get_display_name_from_log()

        if not utils.is_socket_active(socket):
            log.write('Failed to connect to Wayfire IPC socket.\n')
            log.flush()
            raise Exception('Could not connect to Wayfire IPC socket.')

        return wayfire_process, display, socket

def start_app_in_display(app_path: str, display: str):
    """
    Start an application in a specific Wayland display.

    Args:
        app_path (str): Path to the application executable.
        display (str): The Wayland display to use (e.g., 'wayland-2').
    """
    env = os.environ.copy()
    env['WAYLAND_DISPLAY'] = display

    process = Popen([app_path], env=env)

    return process

config = "~/.config/wayfire.ini"
config_path = os.path.expanduser(config)
log_path  = "/tmp/wayfire.log"
wayfire_bin_path = "/usr/bin/wayfire"

process, display, wsock = run_wayfire(wayfire_bin_path, log_path, config_path)

if display:
    start_app_in_display('kitty', display)
    print(wsock.list_views())
