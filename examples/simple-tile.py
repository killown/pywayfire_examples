from wayfire import WayfireSocket
from wayfire.extra.stipc import Stipc
from wayfire.extra.ipc_utils import WayfireUtils

sock = WayfireSocket()
stipc = Stipc(sock)


def create_list_views(layout):
    if "view-id" in layout:
        return [
            (
                layout["view-id"],
                layout["geometry"]["width"],
                layout["geometry"]["height"],
            )
        ]

    split = "horizontal-split" if "horizontal-split" in layout else "vertical-split"
    list = []
    for child in layout[split]:
        list += create_list_views(child)
    return list


def maximize_focused_view():
    focused_view_id = sock.get_focused_view()["id"]
    sock.assign_slot(focused_view_id, "slot_c")


sock.watch()
while True:
    msg = sock.read_next_event()
    if "event" not in msg:
        continue

    if "view-mapped" in msg["event"] or "view-tiled" in msg["event"]:
        view = msg["view"]
        if view["type"] == "toplevel" and view["parent"] == -1:
            if msg["event"] == "view-tiled":
                maximize_focused_view()
                continue

            output = sock.get_output(view["output-id"])
            wset = output["wset-index"]
            wsx = output["workspace"]["x"]
            wsy = output["workspace"]["y"]
            layout = sock.get_tiling_layout(wset, wsx, wsy)
            all_views = create_list_views(layout)

            desired_layout = {}
            if not all_views or (len(all_views) == 1 and all_views[0][0] == view["id"]):
                desired_layout = {
                    "vertical-split": [{"view-id": view["id"], "weight": 1}]
                }
                sock.set_tiling_layout(wset, wsx, wsy, desired_layout)
                continue

            main_view = all_views[0][0]
            weight_main = all_views[0][1]
            stack_views_old = [v for v in all_views[1:] if v[0] != view["id"]]
            weight_others = max(
                [v[1] for v in stack_views_old],
                default=output["workarea"]["width"] - weight_main,
            )

            if main_view == view["id"]:
                continue

            if not stack_views_old:
                desired_layout = {
                    "vertical-split": [
                        {"view-id": main_view, "weight": 2},
                        {"view-id": view["id"], "weight": 1},
                    ]
                }
                sock.set_tiling_layout(wset, wsx, wsy, desired_layout)
                continue

            stack = [{"view-id": v[0], "weight": v[2]} for v in stack_views_old]
            stack += [
                {
                    "view-id": view["id"],
                    "weight": sum([v[2] for v in stack_views_old])
                    / len(stack_views_old),
                }
            ]

            desired_layout = {
                "vertical-split": [
                    {"weight": weight_main, "view-id": main_view},
                    {"weight": weight_others, "horizontal-split": stack},
                ]
            }

            sock.set_tiling_layout(wset, wsx, wsy, desired_layout)
