import time
from wayfire import WayfireSocket

sock = WayfireSocket()

# Configuration
TILE_OUTPUT = "DP-1"
PLUGIN_NAME = "simple-tile"
DELAY_SECONDS = 0.1


def get_current_plugins():
    return sock.get_option_value("core/plugins")["value"].split()


def update_plugins(plugins_list):
    new_value = " ".join(plugins_list)
    sock.set_option_values({"core/plugins": new_value})


# Watch only for output focus changes
sock.watch(["output-gain-focus"])

while True:
    msg = sock.read_next_event()
    if not msg or msg.get("event") != "output-gain-focus":
        continue

    # Hold 100ms to allow compositor state to settle
    time.sleep(DELAY_SECONDS)

    output_name = msg["output"]["name"]
    plugins = get_current_plugins()
    changed = False

    # Logic: Enable if focus gained on TILE_OUTPUT, disable otherwise
    if output_name == TILE_OUTPUT:
        if PLUGIN_NAME not in plugins:
            plugins.append(PLUGIN_NAME)
            changed = True
    else:
        if PLUGIN_NAME in plugins:
            plugins.remove(PLUGIN_NAME)
            changed = True

    if changed:
        update_plugins(plugins)
