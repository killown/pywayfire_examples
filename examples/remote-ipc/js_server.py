import asyncio
import websockets
import json
from wayfire import WayfireSocket
import socket
import struct
import ipaddress
import os

def get_local_network_range():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    netmask = '255.255.255.0'  # Assuming a common local netmask
    ip_bin = struct.unpack('>I', socket.inet_aton(local_ip))[0]
    netmask_bin = struct.unpack('>I', socket.inet_aton(netmask))[0]
    network_bin = ip_bin & netmask_bin
    network_address = socket.inet_ntoa(struct.pack('>I', network_bin))
    cidr_prefix = bin(netmask_bin).count('1')
    return f"{network_address}/{cidr_prefix}"

local_network_range = get_local_network_range()

ALLOWED_IP_RANGES = [
    local_network_range
]

def ip_in_allowed_range(ip):
    return any(ipaddress.ip_address(ip) in ipaddress.ip_network(range) for range in ALLOWED_IP_RANGES)

async def handle_client(websocket, path):
    client_ip = websocket.remote_address[0]

    ip_check_enabled = os.getenv('WAYFIRE_IPC_LAN_ONLY') is not None

    if ip_check_enabled and not ip_in_allowed_range(client_ip):
        await websocket.close()
        return

    sock = WayfireSocket()
    async for message in websocket:
        print(f"Received message: {message}")  # Debugging line

        try:
            data = json.loads(message)
            command = data.get("command")
            args = data.get("args", [])

            if command is None:
                await websocket.send(json.dumps({"error": "Command not specified"}))
                continue

            if not hasattr(sock, command):
                await websocket.send(json.dumps({"error": f"Unknown command: {command}"}))
                continue

            method = getattr(sock, command)

            if not callable(method):
                await websocket.send(json.dumps({"error": f"{command} is not a callable method"}))
                continue

            if not isinstance(args, (list, tuple)):
                args = [args]

            try:
                # Pass arguments to the method
                result = method(*args)
                json_result = json.dumps(result, default=str)
                await websocket.send(json_result)
            except Exception as e:
                await websocket.send(json.dumps({"error": str(e)}))

        except json.JSONDecodeError as e:
            await websocket.send(json.dumps({"error": f"Invalid JSON: {str(e)}"}))

async def main():
    server = await websockets.serve(handle_client, "0.0.0.0", 8787)
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())

