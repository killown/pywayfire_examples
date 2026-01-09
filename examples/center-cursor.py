from wayfire import WayfireSocket
from wayfire.extra.ipc_utils import WayfireUtils as Utils

sock = WayfireSocket()
utils = Utils(sock)

sock.watch(
    [
        "plugin-activation-state-changed",
        "view-focused",
    ]
)

warp_pending = False

while True:
    msg = sock.read_next_event()
    event = msg.get("event")

    if event == "plugin-activation-state-changed":
        if msg.get("state") is True:
            warp_pending = True

    elif event == "view-focused":
        if not warp_pending:
            continue

        view = msg.get("view")
        if not view:
            continue

        if (
            view.get("role") != "toplevel"
            or not view.get("focusable", False)
            or not view.get("mapped", False)
        ):
            continue

        utils.center_cursor_on_view(view["id"])
        warp_pending = False
