import socket
import os
import json
from wayfire import WayfireSocket

socket_path = '/tmp/app_ipc.sock'

if os.path.exists(socket_path):
    os.remove(socket_path)

sock = WayfireSocket()

server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
server_socket.bind(socket_path)
server_socket.listen()

def handle_event(event, conn):
    serialized_event = json.dumps(event)
    conn.sendall((serialized_event + '\n').encode())  # Convert JSON string to bytes

sock.watch()
while True:
    conn, _ = server_socket.accept()
    try:
        while True:
            event = sock.read_next_event()  # Get the event as a dictionary
            handle_event(event, conn)
    except (socket.error, json.JSONDecodeError) as e:
        print(f"Error: {e}")
    finally:
        conn.close()

