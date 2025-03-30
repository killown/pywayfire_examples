import math
import time

from wayfire.extra.stipc import Stipc
from wayfire.ipc import WayfireSocket


def move_in_circles(num_rotations: float, radius: int = 100, center_x: int = None, center_y: int = None):
    """
    Move mouse cursor in continuous circular motion.

    Args:
        num_rotations: Number of full circles to complete
        radius: Pixel radius of circular path
        center_x: Optional fixed center X coordinate
        center_y: Optional fixed center Y coordinate
    """
    sock = WayfireSocket()
    stipc = Stipc(sock)

    if center_x is None or center_y is None:
        center_x, center_y = sock.get_cursor_position()

    steps = int(72 * num_rotations)
    for i in range(steps):
        angle = 2 * math.pi * i / 72
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        stipc.move_cursor(int(x), int(y))
        time.sleep(0.02)


move_in_circles(5)  # 5 circles around current position
move_in_circles(3, radius=150)  # Larger circles
move_in_circles(10, center_x=500, center_y=500)  # Circles around fixed point
