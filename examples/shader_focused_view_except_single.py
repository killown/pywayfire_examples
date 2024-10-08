#!/usr/bin/python3

# A script to apply a shader to all views except the active view
# When a new view is focused, the shader is applied to the previously
# active view. It skips app-id "panel", as this is wf-panel's app-id.

import os
import sys
from wayfire import WayfireSocket
from wayfire.extra.wpe import WPE
from wayfire.extra.ipc_utils import WayfireUtils

# Set shader_path based on arguments or default file
shader_path = None
if len(sys.argv) != 2:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    shader_file = os.path.join(script_dir, "border.shader")
    if os.path.exists(shader_file):
        shader_path = shader_file
    else:
        print(f"Usage: {sys.argv[0]} /path/to/filters/shader")
        sys.exit(-1)
else:
    shader_path = os.path.abspath(sys.argv[1])

sock = WayfireSocket()
wpe = WPE(sock)
utils = WayfireUtils(sock)
sock.watch(['view-focused'])

def has_workspace_single_view():
    views_ac = utils.get_views_from_active_workspace()
    views_ac = [sock.get_view(view_id) for view_id in views_ac]
    toplevel_views = [view for view in views_ac if view and view["role"] == "toplevel" and view["mapped"]]
    return len(toplevel_views) == 1

def unset_view_shaders():
    for view in sock.list_views():
        wpe.filters_unset_view_shader(view["id"])

last_focused_view = None
while True:
    try:
        msg = sock.read_next_event()
        if "event" in msg:
            if has_workspace_single_view():
                continue
            focused_view = sock.get_focused_view()
            if focused_view:
                if focused_view["role"] != "toplevel" or focused_view["mapped"] is False:
                    continue
                if last_focused_view is None:
                    last_focused_view = focused_view["id"]
                elif focused_view["id"] != last_focused_view and focused_view["layer"] == "workspace" and focused_view["fullscreen"] is False:
                    wpe.filters_set_view_shader(focused_view["id"], shader_path)
                    wpe.filters_unset_view_shader(last_focused_view)
                    last_focused_view = focused_view["id"]

    except KeyboardInterrupt:
        unset_view_shaders()
        sys.exit(0)

