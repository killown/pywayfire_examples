# Wayfire IPC: A Comprehensive, Ground-Up Guide

## 1\. Introduction to Inter-Process Communication

Wayfire is a Wayland compositor. Its primary job is to manage the display, draw windows, handle input devices, and route events. However, Wayfire itself is just the core engine. To allow external scripts, status bars, or automation tools to control the window manager, Wayfire implements an Inter-Process Communication (IPC) system.

For a beginner, think of IPC as a "remote control" mechanism. It allows a completely separate program—written in Python, Bash, or Rust—to send commands to Wayfire and receive information back. This guide explains exactly how that remote control is wired, how messages are packaged, and what buttons are available to press, based directly on the Wayfire source code.

## 2\. The Physical Connection: UNIX Domain Sockets

Before two programs can talk, they need a wire between them. Wayfire uses UNIX Domain Sockets for this wire. Unlike network sockets (which use IP addresses and ports to talk across the internet), a UNIX socket uses a file path on your local hard drive to allow local programs to securely communicate.

- When the Wayfire IPC plugin starts, it attempts to create this socket file.
- It first checks if an environment variable named `_WAYFIRE_SOCKET` is set.
- If not, it looks for the `XDG_RUNTIME_DIR` environment variable.
- It creates a file named `wayfire-<display_name>-.socket` inside that directory (or inside `/tmp/` if `XDG_RUNTIME_DIR` is missing).
- Finally, it exports this file path as the `WAYFIRE_SOCKET` environment variable so that child processes know where to connect.

When an external client script wants to talk to Wayfire, it must open this exact socket file path and initiate a connection. Wayfire listens for these new connections by plugging the socket directly into the main Wayland event loop using `wl_event_loop_add_fd`. This means Wayfire checks for IPC messages at the same time it checks for mouse movements or window redraw requests.

## 3\. The Transport Protocol: Length-Prefixed JSON

A socket is just a continuous stream of bytes. If a client sends two messages really fast, Wayfire might read them as one giant chunk of data. To solve this, Wayfire uses a "framing" protocol to define exactly where one message begins and ends.

- Every single message sent over the socket must be formatted as a JSON string.
- However, before the JSON string is sent, the client MUST send a 4-byte integer (in native byte order) representing the exact length of the upcoming JSON string.
- Wayfire reads the 4-byte integer first, allocates a buffer of that exact size, and then reads the exact number of bytes specified to extract the JSON.
- The maximum allowed length for a single JSON message is defined by `MAX_MESSAGE_LEN`, preventing a malicious client from crashing the compositor by sending a gigabyte of text.

### Example Byte Stream

If a client wants to send the message `{"test": true}`, the string is 14 bytes long.

The client sends 18 bytes total:

- Byte 1: 0x0E (14 in decimal)
- Byte 2: 0x00
- Byte 3: 0x00
- Byte 4: 0x00
- Bytes 5-18: `{"test": true}`

## 4\. The Request and Response Cycle

Once the connection and framing are understood, the actual communication follows a strict Server-Client model mapping.

### The Client Request

A client sends a JSON object containing a requested "method". This is essentially the name of the function the client wants Wayfire to execute.

    {
      "method": "window-rules/list-views",
      "data": {}
    }

### The Internal Routing

Inside Wayfire, there is an `ipc::method_repository_t`. This is a lookup table.

- Various plugins register their capabilities into this repository by binding a string name to a C++ function.
- For example, the rules plugin registers "window-rules/list-views" to a C++ function named `list_views`.
- When the JSON request arrives, Wayfire parses it, finds the "method" string, looks it up in the repository, and executes the associated C++ code.

### The Server Response

Once the C++ function finishes running, it returns a JSON object. Wayfire takes this JSON, calculates its length, prepends the 4-byte length integer, and shoots it back across the socket to the client.

    {
      "result": "ok",
      "views": [
        {
          "id": 12,
          "title": "Mozilla Firefox",
          "app-id": "firefox"
        }
      ]
    }

## 5\. Core IPC Capabilities: Window and Workspace Management

The IPC exposes a massive amount of control over the desktop environment. Most of this is handled by the `ipc_rules_t` class.

### Listing Views

- **Method:** "window-rules/list-views".
- **Action:** Returns a massive JSON array of every single window (view) currently tracked by Wayfire.
- **Details:** It includes the view's internal ID, its title, its application ID, its geometry (X, Y, width, height), and what output (monitor) it is currently residing on.

### Listing Outputs and Workspaces

- **Method:** "window-rules/list-outputs".
- **Action:** Returns data about physical monitors.
- **Details:** Includes the monitor's layout geometry, its usable workarea (excluding panels), and its attached workspace set.
- **Method:** "window-rules/list-wsets".
- **Action:** Returns data about workspace grids (e.g., the 3x3 virtual desktop grid). It tells the client which workspace is currently active (e.g., X=1, Y=0).

### Configuring Views

- **Method:** "window-rules/configure-view".
- **Action:** Allows a client to directly manipulate a window.
- **Capabilities:**
  - The client provides the target view's ID.
  - The client can pass a "geometry" object to forcefully resize and move the window.
  - The client can pass "sticky" boolean to make the window appear on all workspaces.
  - The client can set properties dynamically, such as strings, booleans, integers, or floating-point values directly onto the view's property tree.

## 6\. Core IPC Capabilities: Dynamic Configuration

Wayfire reads settings from a file (like `wayfire.ini`), but the IPC allows clients to read and alter these settings live without restarting the compositor. This is managed by the utility methods.

- **Method:** "wayfire/list-config-options".
- **Action:** Dumps every single configuration option available in the compositor.
- **Method:** "wayfire/get-config-option".
- **Action:** Retrieves the current live value of a specific setting.
- **Method:** "wayfire/set-config-options".
- **Action:** Modifies a setting. After the setting is updated in memory, Wayfire emits a `reload_config_signal`. This forces all internal Wayfire plugins to immediately adapt to the new setting, making the change instant.

## 7\. Core IPC Capabilities: Input Simulation and Headless Devices

One of the most powerful features of the Wayfire IPC is its ability to simulate hardware. This is crucial for remote desktop software, testing, or macro scripts.

### Input Device Discovery

- **Method:** "input/list-devices".
- **Action:** Returns a JSON array of all connected hardware keyboards, mice, touchscreens, and drawing tablets.
- **Details:** It queries libinput to extract hardware vendor IDs and product IDs, and exposes whether the device is currently enabled or disabled in the compositor.

### Creating Virtual Hardware

Using wlroots headless backend capabilities, Wayfire can spawn "fake" hardware devices out of thin air.

- It implements custom `wlr_pointer_impl`, `wlr_keyboard_impl`, `wlr_touch_impl`, and `wlr_tablet_impl` structures.
- These fake devices appear to Wayfire exactly like physical USB devices.

### Injecting Raw Input

Once a virtual device exists, a client can use the IPC to send hardware-level signals.

- **Pointer Motion:** A client sends a JSON payload containing dx and dy (delta X and Y). Wayfire injects a `wlr_pointer_motion_event` into the Wayland compositor, moving the mouse cursor exactly as if a physical mouse was pushed.
- **Absolute Pointer Motion:** A client can provide exact X and Y coordinates (between 0.0 and 1.0) to instantly teleport the cursor.
- **Keyboard Events:** A client provides a raw hardware keycode and a state (pressed or released). Wayfire triggers a `wlr_keyboard_key_event`, allowing scripts to type letters or execute keyboard shortcuts as if they were sitting at the physical keyboard.
- **Touch Events:** It supports multi-touch simulation. A client provides a touch_id, coordinates, and a phase (touch down, touch up, touch motion). Wayfire translates this into `wlr_touch_down_event`, making it possible to simulate complex gestures via JSON commands.

## 8\. Asynchronous Event Subscriptions (Watching)

Polling (asking the server for updates 60 times a second) is highly inefficient. Instead, the Wayfire IPC supports real-time event broadcasting.

- **Method:** "window-rules/events/watch".
- **Action:** A client sends an array of event names it cares about (e.g., \["view-geometry-changed", "view-mapped"\]).
- **Mechanism:** Wayfire registers this client in an internal tracking map. It sets up internal hooks into the core Wayfire engine. For instance, it connects to the `view_geometry_changed_signal` inside the window manager.
- **Broadcasting:** Whenever a user manually resizes a window, the Wayfire core emits the signal. The IPC event handler catches this signal, packages the window's old geometry and new geometry into a JSON object, and pushes it across the UNIX socket to any client that subscribed.

### Custom Events

Plugins can emit custom events. If an event name ends in a specific format or is triggered via `custom_event_signal_t`, the IPC will broadcast it. This allows third-party Wayfire plugins to talk to third-party IPC clients without modifying the core IPC source code.

## 9\. Transaction Blocking and Window Interception

The most advanced feature of the IPC is the ability to forcefully freeze the compositor's window rendering pipeline to allow an IPC client to make decisions. This is handled by the PRE_MAP_EVENT system.

### The Wayland Mapping Process

In Wayland, when an application starts, it asks the compositor to "map" its window to the screen. Normally, Wayfire calculates the window size and instantly draws it.

### The IPC Interception

1.  An IPC client subscribes to the "view-pre-map" event.
2.  An application tries to open a window.
3.  Wayfire creates a transaction for this new window but pauses it. It creates an `ipc_delay_object_t` and injects it into the transaction manager.
4.  Wayfire sends the view-pre-map JSON event over the socket to the client, saying "Window ID 45 is trying to open."
5.  Wayfire entirely stops processing that window. The window will remain invisible.
6.  The IPC client (a Python script) analyzes the window. It sees that the window belongs to "Spotify". The script decides it wants Spotify to be exactly 800x600 pixels and moved to Workspace 3.
7.  The script sends "window-rules/configure-view" to apply these changes.
8.  Finally, the script sends the "window-rules/unblock-map" method back to Wayfire.
9.  Wayfire receives the unblock command, removes the `ipc_delay_object_t` from the transaction manager, and resumes drawing.
10. The window finally appears on the screen, exactly where the script wanted it, without ever "flickering" in the wrong location first.

## 10\. Summary of Architectural Flow

To summarize the entire architecture for a beginner from the moment a command is initiated to its completion:

1.  **Preparation:** The IPC Plugin loads and creates `/tmp/wayfire-...socket`.
2.  **Connection:** The client opens the socket and connects. Wayfire registers the file descriptor to `wl_event_loop`.
3.  **Transmission:** The client crafts a JSON object `{ "method": "wayfire/get-config-option", "data": { "option": "core/vwidth" } }`.
4.  **Framing:** The client calculates the byte length of the string (e.g., 85 bytes). It sends \[85 as 4-bytes\]\[The JSON String\].
5.  **Reception:** The Wayfire event loop detects activity on the file descriptor. It reads the 4 bytes, allocates an 85-byte vector, and reads the payload.
6.  **Parsing:** Wayfire parses the string into a `wf::json_t` object.
7.  **Routing:** Wayfire looks at the "method" string and queries the `method_repository`.
8.  **Execution:** The repository routes the call to the `get_config_option` C++ lambda function.
9.  **Interfacing:** The C++ function queries the Wayfire config-manager, retrieves the integer value for core/vwidth, and creates a new `wf::json_t` response.
10. **Return:** The C++ function returns the JSON. The transport layer calculates the response length, prepends the 4-byte header, and writes it back to the socket file descriptor.
11. **Completion:** The client script reads the 4-byte header, reads the JSON, and successfully knows the virtual width of the compositor.

This strict, asynchronous, JSON-over-socket architecture ensures that Wayfire remains fast and stable while exposing infinite scriptability to any language that can read a UNIX socket.
