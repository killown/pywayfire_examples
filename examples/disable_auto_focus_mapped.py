from wayfire import WayfireSocket

sock = WayfireSocket()

last_focused_view_id = sock.get_focused_view()["id"]

sock.watch(["view-mapped", "view-focused"])


def should_continue(msg):
    if "view" in msg:
        if msg["view"] is not None:
            if msg["view"]["role"] == "toplevel":
                return msg["view"]
    return None


while True:
    msg = sock.read_next_event()
    view = should_continue(msg)

    if view is None:
        continue

    if msg["event"] == "view-mapped":
        sock.set_focus(last_focused_view_id)
    if msg["event"] == "view-focused":
        last_focused_view_id = sock.get_focused_view()["id"]
