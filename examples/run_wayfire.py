import os
from subprocess import Popen
from wayfire import WayfireSocket
from wayfire.extra.ipc_utils import WayfireUtils

socket = WayfireSocket()
utils = WayfireUtils(socket)

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

process, display, wsock = utils.run_wayfire(wayfire_bin_path, log_path, config_path)

if display:
    start_app_in_display('kitty', display)
    print(wsock.list_views())
