from wayfire import WayfireSocket

sock = WayfireSocket()
sock.watch()

while True:
    msg = sock.read_next_event()
    if not msg or "event" not in msg:
        continue

    if "view-mapped" in msg["event"]:
        view = msg["view"]

        if view["type"] == "toplevel" and view["parent"] == -1:
            view_id = view["id"]

            sock.set_view_property(view_id, "tiled", False)

            output_id = view["output-id"]
            output = sock.get_output(output_id)
            wset_index = output["wset-index"]
            ws_x = output["workspace"]["x"]
            ws_y = output["workspace"]["y"]

            empty_layout = {"vertical-split": []}

            try:
                sock.set_tiling_layout(wset_index, ws_x, ws_y, empty_layout)
            except Exception:
                pass

            continue
