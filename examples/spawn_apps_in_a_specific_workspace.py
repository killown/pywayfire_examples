import sys

from wayfire import WayfireSocket
from wayfire.extra.stipc import Stipc
from wayfire.extra.ipc_utils import WayfireUtils as Utils

sock = WayfireSocket()
stipc = Stipc(sock)
utils = Utils(sock)

sock.watch(["view-mapped"])
stipc.run_cmd("gedit")

# X is the column index, Y is the row index (0-indexed)
# For a 3x3 grid:
# (0,0) (1,0) (2,0)
# (0,1) (1,1) (2,1)
# (0,2) (1,2) (2,2)
COORDINATES_X = 0
COORDINATES_Y = 1

while True:
    msg = sock.read_next_event()
    view_id = msg["view"]["id"]
    sock.send_view_to_workspace(view_id, COORDINATES_X, COORDINATES_Y)
    workspace_number = utils.get_workspace_number(COORDINATES_X, COORDINATES_Y)
    print(f"Sending the app to workspace {workspace_number}")
    sys.exit()
