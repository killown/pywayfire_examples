import socket
import json

socket_path = '/tmp/app_ipc.sock'

client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
client_socket.connect(socket_path)

def process_event(event):
    print(f"Received event: {event}")

buffer = ""
while True:
    try:
        chunk = client_socket.recv(1024).decode()
        if not chunk:
            break

        buffer += chunk
        while '\n' in buffer:
            event_str, buffer = buffer.split('\n', 1)
            if event_str:
                try:
                    event = json.loads(event_str)
                    process_event(event)
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")

    except socket.error as e:
        print(f"Socket error: {e}")
        break

