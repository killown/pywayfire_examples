#!/usr/bin/env python3

"""
Wayfire output toggle utility.

Supports toggling individual outputs, interactive selection,
disabling all outputs except the currently focused one,
and reloading outputs.

Output modes are detected via wlr-randr and persisted in
~/.config/wayfire_output_config.json for restoration.
"""

from wayfire import WayfireSocket
from subprocess import Popen, check_output
import json
import os
import sys
import re
import time

CONFIG_PATH = os.path.expanduser("~/.config/wayfire_output_config.json")


def load_config():
    """
    Load stored output modes from disk.
    """
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def save_config(data):
    """
    Persist output mode configuration to disk.
    """
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)


def list_known_outputs(sock):
    """
    Return all known outputs, including disabled ones.
    """
    active = {o["name"] for o in sock.list_outputs()}
    stored = set(load_config().keys())
    return sorted(active | stored)


def ask_output(sock):
    """
    Ask the user to select an output interactively.
    """
    outputs = list_known_outputs(sock)

    for i, name in enumerate(outputs):
        print(f"{i}: {name}")

    try:
        idx = int(input("Select output: "))
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)

    return outputs[idx]


def get_current_mode_from_wlr_randr(output_name):
    """
    Detect the current mode of an output using wlr-randr.

    Returns WIDTHxHEIGHT@HZ or None.
    """
    lines = check_output(["wlr-randr"], text=True).splitlines()
    inside = False

    for line in lines:
        if line.startswith(output_name + " "):
            inside = True
            continue

        if inside and re.match(r"^[A-Z].*-\d+", line):
            break

        if inside and "(current)" in line:
            m = re.search(r"(\d+x\d+)\s+px,\s+([\d.]+)\s+Hz", line)
            if m:
                res, hz = m.groups()
                return f"{res}@{hz.replace('.', '')}"

    return None


def turn_off_output(sock, output_name):
    """
    Disable an output and store its current mode.
    """
    config = load_config()
    mode = get_current_mode_from_wlr_randr(output_name)

    if mode:
        config[output_name] = mode
        save_config(config)

    Popen(["wlopm", "--off", output_name])
    sock.set_option_values({f"output:{output_name}": {"mode": "off"}})
    print(f"Turned off {output_name}")


def turn_on_output(sock, output_name):
    """
    Enable an output using the stored or detected mode.
    """
    config = load_config()
    mode = config.get(output_name)

    if not mode:
        mode = get_current_mode_from_wlr_randr(output_name)

    if not mode:
        print(f"No mode available for {output_name}, aborting.")
        return

    sock.set_option_values({f"output:{output_name}": {"mode": mode}})
    print(f"Turned on {output_name} with mode {mode}")


def get_output_state(sock, output_name):
    """
    Return whether an output is currently on or off.
    """
    try:
        mode = sock.get_option_value(f"output:{output_name}/mode")["value"]
    except Exception:
        return "off"

    return "off" if mode == "off" or not mode else "on"


def toggle_output(sock, output_name):
    """
    Toggle the state of an output.
    """
    state = get_output_state(sock, output_name)

    if state == "off":
        turn_on_output(sock, output_name)
    else:
        turn_off_output(sock, output_name)


def disable_except_focused(sock):
    """
    Disable all outputs except the currently focused one.
    """
    focused = sock.get_focused_output()
    focused_name = focused["name"]

    outputs = list_known_outputs(sock)

    for name in outputs:
        if name != focused_name and get_output_state(sock, name) == "on":
            turn_off_output(sock, name)

    print(f"Focused output preserved: {focused_name}")


def reload_output(sock, output_name):
    """
    Reload a single output by disabling and re-enabling it.
    """
    was_on = get_output_state(sock, output_name) == "on"

    if was_on:
        turn_off_output(sock, output_name)
        time.sleep(0.3)

    turn_on_output(sock, output_name)


def reload_all_outputs(sock):
    """
    Reload all known outputs.
    """
    outputs = list_known_outputs(sock)

    for name in outputs:
        reload_output(sock, name)


if __name__ == "__main__":
    sock = WayfireSocket()

    if "--disable-except-focused" in sys.argv:
        disable_except_focused(sock)
        sys.exit(0)

    if "--reload-all" in sys.argv:
        reload_all_outputs(sock)
        sys.exit(0)

    if "--reload" in sys.argv:
        idx = sys.argv.index("--reload")
        try:
            output = sys.argv[idx + 1]
        except IndexError:
            print("Missing output name for --reload")
            sys.exit(1)
        reload_output(sock, output)
        sys.exit(0)

    if len(sys.argv) > 1:
        output = sys.argv[1]
    else:
        output = ask_output(sock)

    toggle_output(sock, output)
