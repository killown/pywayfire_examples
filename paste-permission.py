#!/usr/bin/env python3
"""
Wayfire paste permission controller.

Blocks Ctrl+V globally and allows it only for whitelisted app-ids.
Safely restores state if interrupted.
"""

import json
import sys
from pathlib import Path
from wayfire import WayfireSocket


CONFIG_PATH = Path.home() / ".config" / "paste_permission.json"
BINDING = "<ctrl> KEY_V"


def pretty(obj):
    return json.dumps(obj, indent=2, sort_keys=True)


def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {"allowed_apps": [], "last_binding_id": None}


def save_config(cfg):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


def usage():
    print(
        pretty(
            {
                "usage": {
                    "daemon": "paste-permission.py --daemon",
                    "allow": "paste-permission.py allow <app-id>",
                    "deny": "paste-permission.py deny <app-id>",
                    "list": "paste-permission.py list",
                }
            }
        )
    )


def cli():
    cfg = load_config()
    allowed = set(cfg.get("allowed_apps", []))

    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "list":
        print(pretty({"allowed_apps": sorted(allowed)}))
        return

    if len(sys.argv) < 3:
        usage()
        sys.exit(1)

    app_id = sys.argv[2]

    if cmd == "allow":
        allowed.add(app_id)
    elif cmd == "deny":
        allowed.discard(app_id)
    else:
        usage()
        sys.exit(1)

    cfg["allowed_apps"] = sorted(allowed)
    save_config(cfg)
    print(pretty(cfg))


class PasteGuard:
    """
    Controls Ctrl+V based on focused view app-id.
    """

    def __init__(self, sock):
        self.sock = sock
        self.cfg = load_config()
        self.allowed = set(self.cfg.get("allowed_apps", []))
        self.binding_id = None
        self.blocked = False
        self.sock.clear_bindings()
        self._cleanup_stale_binding()
        self.block()

    def _cleanup_stale_binding(self):
        stale = self.cfg.get("last_binding_id")
        if stale:
            try:
                self.sock.unregister_binding(stale)
            except Exception:
                pass
            self.cfg["last_binding_id"] = None
            save_config(self.cfg)

    def block(self):
        if self.blocked:
            return
        resp = self.sock.register_binding(
            BINDING,
            command="true",
            exec_always=True,
            mode="normal",
        )
        self.binding_id = resp["binding-id"]
        self.cfg["last_binding_id"] = self.binding_id
        save_config(self.cfg)
        self.blocked = True

    def allow(self):
        if not self.blocked:
            return
        self.sock.unregister_binding(self.binding_id)
        self.binding_id = None
        self.cfg["last_binding_id"] = None
        save_config(self.cfg)
        self.blocked = False

    def on_focus(self, view):
        if not isinstance(view, dict):
            self.block()
            return

        app_id = view.get("app-id") or view.get("app_id")
        if not app_id:
            self.block()
            return

        if app_id in self.allowed:
            self.allow()
        else:
            self.block()


def daemon():
    sock = WayfireSocket()
    guard = PasteGuard(sock)
    sock.watch(["view-focused"])

    while True:
        event = sock.read_next_event()
        guard.on_focus(event.get("view"))


def main():
    if len(sys.argv) == 1:
        usage()
        return

    if sys.argv[1] == "--daemon":
        daemon()
        return

    cli()


if __name__ == "__main__":
    main()
