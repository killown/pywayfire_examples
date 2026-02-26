from wayfire import WayfireSocket
from wayfire.extra.stipc import Stipc

sock = WayfireSocket()
stipc = Stipc(sock)


def move_to_output_center(output_name: str) -> None:
    """Moves the cursor to the center coordinates of a specific output Name."""
    outputs = sock.list_outputs()
    for output in outputs:
        if output["name"] == output_name:
            geo = output["geometry"]
            center_x = geo["x"] + (geo["width"] // 2)
            center_y = geo["y"] + (geo["height"] // 2)
            stipc.move_cursor(center_x, center_y)
            stipc.click_button("BTN_LEFT", "full")
            break


move_to_output_center("DP-1")
