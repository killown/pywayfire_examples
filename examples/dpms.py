import time
from wayfire import WayfireSocket
from wayfire.extra.stipc import Stipc
import subprocess

TIMEOUT_SECONDS = 600
SUSPEND_TIMEOUT_SECONDS = -1  # Set to -1 to disable suspend
POLL_INTERVAL_SECONDS = 1


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

        for name in list(outputs_state.keys()):
            if name not in current_outputs_info:
                if not outputs_state[name]["dpms_on"]:
                    stipc.run_cmd(f"wlopm --on '{name}'")
                del outputs_state[name]

        for name, data in outputs_state.items():
            if name in current_outputs_info:
                data["geometry"] = current_outputs_info[name]["geometry"]

        cursor_pos = sock.get_cursor_position()
        focused_output_info = sock.get_focused_output()
        active_outputs_by_fullscreen = {
            view["output-name"] for view in sock.list_views() if view.get("fullscreen")
        }

        any_output_active = False

        for name, state in outputs_state.items():
            is_active_due_to_fullscreen = name in active_outputs_by_fullscreen

            if is_active_due_to_fullscreen:
                state["counter"] = 0
                if not state["dpms_on"]:
                    stipc.run_cmd(f"wlopm --on '{name}'")
                    state["dpms_on"] = True
                any_output_active = True
                continue

            if focused_output_info and name == focused_output_info["name"]:
                if last_cursor_pos == cursor_pos:
                    state["counter"] += POLL_INTERVAL_SECONDS
                else:
                    state["counter"] = 0
                    any_output_active = True

                if state["counter"] >= TIMEOUT_SECONDS and state["dpms_on"]:
                    stipc.run_cmd(f"wlopm --off '{name}'")
                    state["dpms_on"] = False
                elif state["counter"] < TIMEOUT_SECONDS and not state["dpms_on"]:
                    stipc.run_cmd(f"wlopm --on '{name}'")
                    state["dpms_on"] = True
            else:
                state["counter"] += POLL_INTERVAL_SECONDS
                if state["counter"] >= TIMEOUT_SECONDS and state["dpms_on"]:
                    stipc.run_cmd(f"wlopm --off '{name}'")
                    state["dpms_on"] = False
                elif state["counter"] < TIMEOUT_SECONDS and not state["dpms_on"]:
                    stipc.run_cmd(f"wlopm --on '{name}'")
                    state["dpms_on"] = True

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
