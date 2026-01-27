# MIT License
#
# Copyright (c) 2025 Thiago <killown.matrix@gmail.com> (killown)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import gi
from gi.repository import GLib
import subprocess
import wayfire
import tempfile
import os
from PIL import Image, ImageChops, ImageStat

# === Config ===
TIMEOUT_SECONDS = 600  # Per-output DPMS off timeout
SUSPEND_TIMEOUT_SECONDS = 7200  # Global suspend timeout (-1 to disable)
POLL_INTERVAL_SECONDS = 5  # How often to poll cursor/outputs

# === State ===
outputs_state = {}
inactivity_counter = {"value": 0}
last_cursor_pos = None

# === Wayfire socket ===
wf_socket = wayfire.WayfireSocket()
wf_socket.watch(["output-gain-focus", "plugin-activation-state-changed"])


# Wayfire DPMS Manager
# Monitors outputs, cursor, and fullscreen views to manage DPMS and suspend.
# Each output has its own inactivity counter and baseline screenshot.
# Cursor movement inside an output resets its counter.
# Screenshots are compared before turning off an output to detect visual changes.
# Minor changes such as a blinking cursor or small animations are ignored.
# Fullscreen views prevent DPMS off and reset counters.
# Global inactivity across all outputs triggers system suspend.
# Wayfire events (focus gain, plugin activation) wake outputs and reset counters.
# External commands (wlopm, systemctl) are run non-blocking via subprocess.Popen.
# Uses GLib MainLoop with IO watch on Wayfire socket and periodic polling.


def cursor_in_geometry(cursor, geometry):
    try:
        x, y = cursor
        gx, gy = int(geometry["x"]), int(geometry["y"])
        gw, gh = int(geometry["width"]), int(geometry["height"])
        return gx <= x < gx + gw and gy <= y < gy + gh
    except Exception:
        return False


def safe_run(cmd):
    try:
        subprocess.Popen(cmd)
    except Exception as e:
        print(f"[error] Failed to run {cmd}: {e}")


def screenshot_output(output_name):
    """Take a screenshot of one output using grim, return PIL.Image or None."""
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmp.close()
        subprocess.run(
            ["grim", "-o", output_name, tmp.name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        img = Image.open(tmp.name).convert("RGB")
        os.unlink(tmp.name)
        return img
    except Exception as e:
        print(f"[error] Screenshot failed for {output_name}: {e}")
        return None


def images_changed(img1, img2, threshold=0.001):
    if img1 is None or img2 is None:
        return False
    diff = ImageChops.difference(img1, img2)
    stat = ImageStat.Stat(diff)
    # Mean pixel difference across channels
    mean_diff = sum(stat.mean) / len(stat.mean)
    # Normalize to 0–255
    relative_change = mean_diff / 255.0
    return relative_change > threshold


def wake_on_wf_event(source, condition):
    if condition & GLib.IO_IN:
        try:
            event = wf_socket.read_next_event()
        except Exception as e:
            print("[error] Failed to read Wayfire event:", e)
            return True

        etype = event.get("event")

        if etype == "output-gain-focus":
            out_name = event.get("output", {}).get("name")
            state = outputs_state.get(out_name)
            if state and not state["dpms_on"]:
                safe_run(["wlopm", "--on", out_name])
                state["dpms_on"] = True
                state["counter"] = 0
            inactivity_counter["value"] = 0

        elif etype == "plugin-activation-state-changed":
            out_info = event.get("output-data", {})
            out_name = out_info.get("name")
            state = outputs_state.get(out_name)
            if state and not state["dpms_on"]:
                safe_run(["wlopm", "--on", out_name])
                state["dpms_on"] = True
                state["counter"] = 0
            inactivity_counter["value"] = 0

    return True


def poll_cursor_and_outputs():
    global last_cursor_pos

    try:
        cursor_pos = wf_socket.get_cursor_position()
        outputs = wf_socket.list_outputs()
        views = wf_socket.list_views()
    except Exception as e:
        print("[error] Failed to poll Wayfire state:", e)
        return True

    # Update outputs state
    for o in outputs:
        name = o.get("name")
        if not name:
            continue
        if name not in outputs_state:
            outputs_state[name] = {
                "geometry": o["geometry"],
                "counter": 0,
                "dpms_on": True,
                "baseline": None,
            }
        else:
            outputs_state[name]["geometry"] = o["geometry"]

    cursor_moved = (last_cursor_pos is None) or (last_cursor_pos != cursor_pos)

    for name, state in outputs_state.items():
        fullscreen_active = any(
            v.get("fullscreen") and v.get("output-name") == name for v in views
        )

        if fullscreen_active:
            if not state["dpms_on"]:
                safe_run(["wlopm", "--on", name])
                state["dpms_on"] = True
            state["counter"] = 0
            state["baseline"] = None
            continue

        if state["dpms_on"]:
            if cursor_moved and cursor_in_geometry(cursor_pos, state["geometry"]):
                # Reset only this output if cursor moved inside it
                state["counter"] = 0
                state["baseline"] = None
            else:
                state["counter"] += POLL_INTERVAL_SECONDS

                # Take baseline at counter == 0
                if state["counter"] == POLL_INTERVAL_SECONDS:
                    state["baseline"] = screenshot_output(name)

                # Just before timeout, compare screenshots
                if state["counter"] >= TIMEOUT_SECONDS:
                    new_shot = screenshot_output(name)
                    if images_changed(state["baseline"], new_shot):
                        print(f"[info] Output {name} updated, keeping on")
                        state["counter"] = 0
                        state["baseline"] = new_shot
                    else:
                        safe_run(["wlopm", "--off", name])
                        state["dpms_on"] = False
                        state["counter"] = 0
                        state["baseline"] = None

    # Global inactivity
    if any(state["dpms_on"] for state in outputs_state.values()):
        inactivity_counter["value"] = 0
    else:
        inactivity_counter["value"] += POLL_INTERVAL_SECONDS

    if (
        SUSPEND_TIMEOUT_SECONDS != -1
        and inactivity_counter["value"] >= SUSPEND_TIMEOUT_SECONDS
    ):
        safe_run(["systemctl", "suspend"])
        inactivity_counter["value"] = 0

    last_cursor_pos = cursor_pos
    return True


# === Main loop setup ===
GLib.io_add_watch(wf_socket.client.fileno(), GLib.IO_IN, wake_on_wf_event)
GLib.timeout_add_seconds(POLL_INTERVAL_SECONDS, poll_cursor_and_outputs)

loop = GLib.MainLoop()
loop.run()
