from wayfire import WayfireSocket


def turn_off_output(sock, output_name="DP-2"):
    """
    Turn off the specified output.
    """
    # Set the mode to "off" to disable the output
    sock.set_option_values({f"output:{output_name}": {"mode": "off"}})
    print(f"Turned off {output_name}.")


def turn_on_output(sock, output_name="DP-2", mode="1920x1080@144000"):
    """
    Turn on the specified output with the given mode.
    """
    # Set the mode to the specified resolution to enable the output
    sock.set_option_values({f"output:{output_name}": {"mode": mode}})
    print(f"Turned on {output_name} with mode {mode}.")


def get_output_state(sock, output_name="DP-2"):
    """
    Get the current state of the output (on or off).
    """
    # Query the current mode of the output
    mode = sock.get_option_value(f"output:{output_name}/mode")["value"]
    # If the mode is "off" or empty, the output is off; otherwise, it's on
    return "off" if mode == "off" or not mode else "on"


def toggle_output(sock, output_name="DP-2", mode="1920x1080@144000"):
    """
    Toggle the output state (off if on, on if off).
    """
    current_state = get_output_state(sock, output_name)
    if current_state == "off":
        turn_on_output(sock, output_name, mode)
    else:
        turn_off_output(sock, output_name)


# Example usage
if __name__ == "__main__":
    # Initialize the WayfireSocket
    sock = WayfireSocket()

    # Toggle the output state
    toggle_output(sock, output_name="DP-2", mode="1920x1080@144000")
