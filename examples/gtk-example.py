import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
from wayfire import WayfireSocket 

class WayfireEventApp(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sock = WayfireSocket()  # Initialize WayfireSocket
        self.sock.watch(["event"])
        GLib.io_add_watch(self.sock.client, GLib.IO_IN, self.on_event_ready)
        self.setup_event_watch()
        self.label = None

    def do_activate(self):
        window = Gtk.ApplicationWindow(application=self)
        window.set_title("Wayfire Event Viewer")
        window.set_default_size(400, 200)

        self.label = Gtk.Label(label="Waiting for events...")
        window.set_child(self.label)
        window.show()

    def on_event_ready(self, fd, condition):
        # This function is called when the file descriptor is ready for reading
        try:
            msg = self.sock.read_next_event()
            if msg is not None:
                self.handle_event(msg)
        except Exception as e:
            print(f"Error processing Wayfire events: {e}")

        # Return True to continue calling this function
        return True

    def handle_event(self, msg):
        # Process the Wayfire event and update the GUI
        if 'view-focused' in msg["event"]:
            view_key = msg['view']["title"]
            self.label.set_label(f"Focused View Key: {view_key}")

if __name__ == "__main__":
    app = WayfireEventApp()
    app.run()
