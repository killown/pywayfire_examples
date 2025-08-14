from wayfire import WayfireSocket
from wayfire.extra.stipc import Stipc
from wayfire.extra.ipc_utils import WayfireUtils
import sqlite3
import json
from pathlib import Path
import time

sock = WayfireSocket()
stipc = Stipc(sock)
utils = WayfireUtils(sock)


def get_exe_path(pid):
    try:
        return str(Path(f"/proc/{pid}/exe").resolve())
    except Exception:
        return None


db_path = Path.home() / ".config" / "wayfire_views.db"
db_path.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(db_path)

try:
    for row in conn.execute("SELECT view FROM views"):
        saved = json.loads(row[0])
        exe = saved.get("exe")
        if exe:
            result = stipc.run_cmd(exe)
            pid = result.get("pid")
            if not pid:
                continue
            time.sleep(3)
            new_views = [
                v
                for v in sock.list_views()
                if v["pid"] == pid and v["role"] == "toplevel"
            ]
            if not new_views:
                continue
            new_view_id = new_views[0]["id"]
            geo = saved["geometry"]
            output_id = saved["output_id"]
            ws = saved["workspace"]
            if saved["fullscreen"]:
                sock.set_view_fullscreen(new_view_id, True)
            else:
                sock.configure_view(
                    new_view_id,
                    geo["x"],
                    geo["y"],
                    geo["width"],
                    geo["height"],
                    output_id,
                )
            sock.set_workspace(ws["x"], ws["y"], new_view_id)
except sqlite3.OperationalError:
    pass

conn.execute("DROP TABLE IF EXISTS views")
conn.execute("CREATE TABLE views (view JSON)")
conn.commit()

current_views = []
for v in sock.list_views():
    if v["role"] == "toplevel":
        ws = utils.get_workspace_from_view(v["id"])
        if ws is None:
            continue
        full_view = dict(v)
        full_view["workspace"] = {"x": ws["x"], "y": ws["y"]}
        full_view["exe"] = get_exe_path(v["pid"])
        current_views.append(full_view)

conn.execute("DELETE FROM views")
conn.executemany(
    "INSERT INTO views (view) VALUES (?)", [(json.dumps(v),) for v in current_views]
)
conn.commit()

for row in conn.execute("SELECT view FROM views"):
    print(row[0])

sock.watch(["view-mapped", "view-unmapped"])

while True:
    sock.read_next_event()
    current_views = []
    for v in sock.list_views():
        if v["role"] == "toplevel":
            ws = utils.get_workspace_from_view(v["id"])
            if ws is None:
                continue
            full_view = dict(v)
            full_view["workspace"] = {"x": ws["x"], "y": ws["y"]}
            full_view["exe"] = get_exe_path(v["pid"])
            current_views.append(full_view)
    conn.execute("DELETE FROM views")
    conn.executemany(
        "INSERT INTO views (view) VALUES (?)", [(json.dumps(v),) for v in current_views]
    )
    conn.commit()
    for row in conn.execute("SELECT view FROM views"):
        print(row[0])
