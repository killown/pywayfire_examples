import asyncio
import os
import json
from concurrent.futures import ThreadPoolExecutor
from wayfire import WayfireSocket

socket_paths = ['/tmp/waypanel.sock', '/tmp/waypanel-dockbar.sock']

for path in socket_paths:
    if os.path.exists(path):
        os.remove(path)

sock = WayfireSocket()

sock.watch()

executor = ThreadPoolExecutor()

event_queue = asyncio.Queue()

def read_events():
    while True:
        event = sock.read_next_event()  # blocking call
        asyncio.run_coroutine_threadsafe(event_queue.put(event), loop)

# handle events and send them to connected clients
async def handle_event(clients):
    while True:
        event = await event_queue.get()
        serialized_event = json.dumps(event)
        # Broadcast the event to all connected clients
        for client in clients:
            try:
                client.write((serialized_event + '\n').encode())
                await client.drain()
            except (ConnectionResetError, BrokenPipeError):
                clients.remove(client)  # Remove clients that have disconnected

async def handle_client(reader, writer, clients):
    clients.append(writer)
    try:
        while True:
            await asyncio.sleep(3600)  # Keep the client connection alive
    except (ConnectionResetError, BrokenPipeError):
        pass
    finally:
        clients.remove(writer)
        writer.close()
        await writer.wait_closed()

# start a server for a given path
async def start_server(path, clients):
    server = await asyncio.start_unix_server(lambda r, w: handle_client(r, w, clients), path=path)
    async with server:
        await server.serve_forever()

async def main():
    clients = []
    servers = [start_server(path, clients) for path in socket_paths]
    # Start the event reader in a separate thread
    global loop
    loop = asyncio.get_running_loop()
    executor.submit(read_events)
    await asyncio.gather(*servers, handle_event(clients))

if __name__ == '__main__':
    asyncio.run(main())

