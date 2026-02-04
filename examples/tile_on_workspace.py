import time
from wayfire import WayfireSocket

sock = WayfireSocket()

TILE_WORKSPACE = (0, 1)
PLUGIN_NAME = "simple-tile"
DELAY_SECONDS = 0.6


def get_current_plugins():
    return sock.get_option_value("core/plugins")["value"].split()


def update_plugins(plugins_list):
    new_value = " ".join(plugins_list)
    sock.set_option_values({"core/plugins": new_value})


sock.watch(["wset-workspace-changed"])

while True:
    msg = sock.read_next_event()
    if not msg or msg.get("event") != "wset-workspace-changed":
        continue

    time.sleep(DELAY_SECONDS)

    new_ws = msg.get("new-workspace")
    current_coords = (new_ws["x"], new_ws["y"])

    plugins = get_current_plugins()
    changed = False

    if current_coords == TILE_WORKSPACE:
        if PLUGIN_NAME not in plugins:
            plugins.append(PLUGIN_NAME)
            changed = True
    else:
        if PLUGIN_NAME in plugins:
            plugins.remove(PLUGIN_NAME)
            changed = True

    if changed:
        update_plugins(plugins)
