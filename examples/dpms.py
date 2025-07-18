from wayfire import WayfireSocket
from wayfire.extra.stipc import Stipc
import time

sock = WayfireSocket()
stipc = Stipc(sock)


TIMEOUT = 1800


def dpms_off():
    stipc.run_cmd("wlopm --off DP-1")
    stipc.run_cmd("wlopm --off DP-2")


def dpms_on():
    stipc.run_cmd("wlopm --on DP-1")
    stipc.run_cmd("wlopm --on DP-2")


def is_any_view_fullscreen():
    return any(view for view in sock.list_views() if view["fullscreen"] is True)


current_cursor_position = sock.get_cursor_position()

counter = 0
dpms_is_on = True
while True:
    time.sleep(1)
    cursor_position = sock.get_cursor_position()

    # reset the timeout counter
    if cursor_position != current_cursor_position:
        if dpms_is_on is False:
            dpms_on()
        counter = 0
        dpms_is_on = True
        current_cursor_position = cursor_position

    counter += 1

    if counter >= TIMEOUT and dpms_is_on is True:
        if is_any_view_fullscreen():
            counter = 0
            continue
        else:
            dpms_is_on = False
            dpms_off()
