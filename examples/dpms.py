import time
from wayfire import WayfireSocket
from wayfire.extra.stipc import Stipc
import subprocess

TIMEOUT_SECONDS = 1800
SUSPEND_TIMEOUT_SECONDS = 7200
POLL_INTERVAL_SECONDS = 60


def cursor_in_geometry(cursor, geometry):
    x, y = cursor
    gx = int(geometry["x"])
    gy = int(geometry["y"])
    gw = int(geometry["width"])
    gh = int(geometry["height"])
    return gx <= x < gx + gw and gy <= y < gy + gh


def main():
    sock = WayfireSocket()
    stipc = Stipc(sock)
    outputs_state = {}
    last_cursor_pos = None
    global_inactivity_counter = 0

    while True:
        current_outputs_info = {o["name"]: o for o in sock.list_outputs()}

        for name, data in current_outputs_info.items():
            if name not in outputs_state:
                outputs_state[name] = {
                    "geometry": data["geometry"],
                    "counter": 0,
                    "dpms_on": True,
                }
            else:
                outputs_state[name]["geometry"] = data["geometry"]

        for name in list(outputs_state.keys()):
            if name not in current_outputs_info:
                if not outputs_state[name]["dpms_on"]:
                    stipc.run_cmd(f"wlopm --on '{name}'")
                del outputs_state[name]

        cursor_pos = sock.get_cursor_position()
        views = sock.list_views()
        any_output_active = False

        for name, state in outputs_state.items():
            fullscreen_active = any(
                v.get("fullscreen") and v.get("output-name") == name for v in views
            )
            if fullscreen_active:
                if not state["dpms_on"]:
                    stipc.run_cmd(f"wlopm --on '{name}'")
                    state["dpms_on"] = True
                state["counter"] = 0
                any_output_active = True
                continue

            if state["dpms_on"]:
                if last_cursor_pos != cursor_pos and cursor_in_geometry(
                    cursor_pos, state["geometry"]
                ):
                    state["counter"] = 0
                    any_output_active = True
                else:
                    state["counter"] += POLL_INTERVAL_SECONDS
                if state["counter"] >= TIMEOUT_SECONDS:
                    stipc.run_cmd(f"wlopm --off '{name}'")
                    state["dpms_on"] = False
                    state["counter"] = 0
            else:
                if last_cursor_pos != cursor_pos and cursor_in_geometry(
                    cursor_pos, state["geometry"]
                ):
                    stipc.run_cmd(f"wlopm --on '{name}'")
                    state["dpms_on"] = True
                    state["counter"] = 0
                    any_output_active = True

        if any_output_active or cursor_pos != last_cursor_pos:
            global_inactivity_counter = 0
        else:
            global_inactivity_counter += POLL_INTERVAL_SECONDS

        if (
            SUSPEND_TIMEOUT_SECONDS != -1
            and global_inactivity_counter >= SUSPEND_TIMEOUT_SECONDS
        ):
            subprocess.run(["systemctl", "suspend"])
            global_inactivity_counter = 0

        last_cursor_pos = cursor_pos
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
