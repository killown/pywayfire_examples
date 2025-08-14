from wayfire import WayfireSocket
from wayfire.extra.stipc import Stipc
import sqlite3
import json
from pathlib import Path
import subprocess
import time

sock = WayfireSocket()
stipc = Stipc(sock)


def get_exe_path(pid):
    try:
        return str(Path(f"/proc/{pid}/exe").resolve())
    except Exception:
        return None


db_path = Path.home() / ".config" / "wayfire_views.db"
db_path.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(db_path)

for row in conn.execute("SELECT exe, view FROM views"):
    exe = row[0]
    saved_view = json.loads(row[1])
    if exe:
        pid = stipc.run_cmd(exe)["pid"]
        time.sleep(1)
        print(pid)
        new_view_id = [view["id"] for view in sock.list_views() if view["pid"] == pid][
            0
        ]
        geo = saved_view["geometry"]
        sock.configure_view(
            new_view_id, geo["x"], geo["y"], geo["width"], geo["height"]
        )

conn.execute("DROP TABLE IF EXISTS views")
conn.execute("CREATE TABLE views (pid INTEGER, exe TEXT, view JSON)")
conn.commit()

views = [v for v in sock.list_views() if v["role"] == "toplevel"]
data = [(v["pid"], get_exe_path(v["pid"]), json.dumps(v)) for v in views]
conn.execute("DELETE FROM views")
conn.executemany("INSERT INTO views (pid, exe, view) VALUES (?, ?, ?)", data)
conn.commit()

for row in conn.execute("SELECT exe, view FROM views"):
    view = json.loads(row[1])
    print(f"{row[0]}: {view}")

sock.watch(["view-mapped", "view-unmapped"])

while True:
    sock.read_next_event()
    views = [v for v in sock.list_views() if v["role"] == "toplevel"]
    data = [(v["pid"], get_exe_path(v["pid"]), json.dumps(v)) for v in views]
    conn.execute("DELETE FROM views")
    conn.executemany("INSERT INTO views (pid, exe, view) VALUES (?, ?, ?)", data)
    conn.commit()
    for row in conn.execute("SELECT exe, view FROM views"):
        view = json.loads(row[1])
        print(f"{row[0]}: {view}")
