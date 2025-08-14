from wayfire import WayfireSocket
import sqlite3
import json
from pathlib import Path

sock = WayfireSocket()


def get_exe_path(pid):
    try:
        return str(Path(f"/proc/{pid}/exe").resolve())
    except Exception:
        return None


db_path = Path.home() / ".config" / "wayfire_views.db"
db_path.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(db_path)
conn.execute("DROP TABLE IF EXISTS views")
conn.execute("CREATE TABLE views (pid INTEGER, exe TEXT, view JSON)")
conn.commit()

sock.watch(["view-mapped", "view-unmapped"])

while True:
    sock.read_next_event()
    views = [v for v in sock.list_views() if v["role"] == "toplevel"]
    data = [(v["pid"], get_exe_path(v["pid"]), json.dumps(v)) for v in views]
    conn.execute("DELETE FROM views")
    conn.executemany("INSERT INTO views (pid, exe, view) VALUES (?, ?, ?)", data)
    conn.commit()
    # here is how you list all the saved views
    for row in conn.execute("SELECT exe, view FROM views"):
        view = json.loads(row[1])
        print(f"{row[0]}: {view}")
