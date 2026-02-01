import subprocess
import asyncio
from wayfire import WayfireSocket


def get_absolute_geometry():
    sock = WayfireSocket()

    view = sock.get_focused_view()
    output = sock.get_focused_output()

    if not view or not output:
        return None

    # Calculate absolute position
    abs_x = output["geometry"]["x"] + view["geometry"]["x"]
    abs_y = output["geometry"]["y"] + view["geometry"]["y"]
    width = view["geometry"]["width"]
    height = view["geometry"]["height"]

    return f"{abs_x},{abs_y} {width}x{height}"


async def capture_view():
    region = get_absolute_geometry()
    if not region:
        return

    output_path = "focused_view.png"

    # Using grim with the calculated global geometry
    try:
        subprocess.run(["grim", "-g", region, output_path], check=True)
    except FileNotFoundError:
        pass


if __name__ == "__main__":
    asyncio.run(capture_view())
