from wayfire import WayfireSocket
import sys
import os

sock = WayfireSocket()

KEYBIND = "<ctrl><alt> KEY_E"

# NOTE: actually, you can do the following:
#         def register_binding():
#            print("Registering binding")
#            return sock.register_binding(
#                binding="<ctrl><alt> KEY_E",
#                call_method="expo/toggle",
#                call_data={},
#                exec_always=True,
#                mode="normal",
#          )
# but this example is about how to bind custom scripts with command
script_content = """from wayfire import WayfireSocket

sock = WayfireSocket()
sock.toggle_expo()
"""


# instead of having two files, one for binding and another which contains the script,
# we do all inside one file just as example.
def create_script_file(path):
    script_path = path
    if os.path.exists(script_path):
        print(f"Script already exists at {script_path}")
        return None

    os.makedirs(os.path.dirname(script_path), exist_ok=True)

    with open(script_path, "w") as f:
        f.write(script_content)
    return script_path


def add_keybind():
    script_path = "/tmp/.my_keybind_script.py"

    # Check if a path was provided as command line argument, so you could append custom scripts
    if len(sys.argv) > 1:
        script_path = sys.argv[1]

    created_path = create_script_file(script_path)

    # Only register keybind if we actually created a new file
    if created_path:
        sock.clear_bindings()
        sock.register_binding(
            binding=KEYBIND,
            command=f"python3 {created_path}",
            exec_always=True,
            mode="normal",
        )
        print(f"Registered keybind: {KEYBIND}")
    else:
        print("Keybind not registered, script already exists")


add_keybind()
