import gi

gi.require_version("GLib", "2.0")
from gi.repository import GLib
import subprocess
import wayfire

TIMEOUT_SECONDS = 600
SUSPEND_TIMEOUT_SECONDS = 7200
POLL_INTERVAL_SECONDS = 5

outputs_state = {}
inactivity_counter = {"value": 0}
last_cursor_pos = None

wf_socket = wayfire.WayfireSocket()
wf_socket.watch(["output-gain-focus", "plugin-activation-state-changed"])


def cursor_in_geometry(cursor, geometry):
    """
    Check if the cursor is inside the given geometry.
    """
    x, y = cursor
    gx = int(geometry["x"])
    gy = int(geometry["y"])
    gw = int(geometry["width"])
    gh = int(geometry["height"])
    return gx <= x < gx + gw and gy <= y < gy + gh


def wake_on_wf_event(source, condition):
    """
    Handle Wayfire events to wake monitors and reset counters.
    """
    if condition & GLib.IO_IN:
        event = wf_socket.read_next_event()
        etype = event.get("event")

        if etype == "output-gain-focus":
            out_name = event["output"]["name"]
            state = outputs_state.get(out_name)
            if state and not state["dpms_on"]:
                subprocess.run(["wlopm", "--on", out_name])
                state["dpms_on"] = True
                state["counter"] = 0
            inactivity_counter["value"] = 0

        elif etype == "plugin-activation-state-changed":
            out_info = event.get("output-data", {})
            out_name = out_info.get("name")
            state = outputs_state.get(out_name)
            if state and not state["dpms_on"]:
                subprocess.run(["wlopm", "--on", out_name])
                state["dpms_on"] = True
                state["counter"] = 0
            inactivity_counter["value"] = 0
    return True


def poll_cursor_and_outputs():
    """
    Periodically poll cursor position, outputs, and fullscreen views to manage DPMS.
    """
    global last_cursor_pos

    cursor_pos = wf_socket.get_cursor_position()
    outputs = wf_socket.list_outputs()
    views = wf_socket.list_views()

    for o in outputs:
        name = o["name"]
        if name not in outputs_state:
            outputs_state[name] = {
                "geometry": o["geometry"],
                "counter": 0,
                "dpms_on": True,
            }
        else:
            outputs_state[name]["geometry"] = o["geometry"]

    for name, state in outputs_state.items():
        fullscreen_active = any(
            v.get("fullscreen") and v.get("output-name") == name for v in views
        )

        if fullscreen_active:
            if not state["dpms_on"]:
                subprocess.run(["wlopm", "--on", name])
                state["dpms_on"] = True
            state["counter"] = 0
            continue

        if state["dpms_on"]:
            if last_cursor_pos != cursor_pos and cursor_in_geometry(
                cursor_pos, state["geometry"]
            ):
                state["counter"] = 0
            else:
                state["counter"] += POLL_INTERVAL_SECONDS
                if state["counter"] >= TIMEOUT_SECONDS:
                    subprocess.run(["wlopm", "--off", name])
                    state["dpms_on"] = False
                    state["counter"] = 0

    if any(state["dpms_on"] for state in outputs_state.values()):
        inactivity_counter["value"] = 0
    else:
        inactivity_counter["value"] += POLL_INTERVAL_SECONDS

    if (
        SUSPEND_TIMEOUT_SECONDS != -1
        and inactivity_counter["value"] >= SUSPEND_TIMEOUT_SECONDS
    ):
        subprocess.run(["systemctl", "suspend"])
        inactivity_counter["value"] = 0

    last_cursor_pos = cursor_pos
    return True


GLib.io_add_watch(wf_socket.client.fileno(), GLib.IO_IN, wake_on_wf_event)
GLib.timeout_add_seconds(POLL_INTERVAL_SECONDS, poll_cursor_and_outputs)

loop = GLib.MainLoop()
loop.run()
