import asyncio
import os

import aiohttp

from firecracker.setup import vm_id, jailer_path, socket_path, vsock_path, set_kernel, set_rootfs, \
    set_vsock, set_network, cleanup_jailer, setfacl, start_jailed_firecracker, start_machine, \
    configure_vm


async def main():
    await setfacl()

    proc = None
    try:
        print(f"./firecracker.bin --api-sock {socket_path}")
        if not input("Using existing Firecracker here ?"):
            cleanup_jailer()
            if os.path.exists(path=socket_path):
                os.remove(path=socket_path)
            # proc = await start_firecracker()
            proc = await start_jailed_firecracker()
            print("Waiting a bit...")
            await asyncio.sleep(0.5)
            print("Waited")
        else:
            proc = None

        conn = aiohttp.UnixConnector(path=socket_path)
        session = aiohttp.ClientSession(connector=conn)
        await configure_vm(session)

        await start_machine(session)

        print("Waiting for start")
        queue = asyncio.Queue()
        async def unix_client_connected(*args):
            print('args', args)
            await queue.put(True)
        await asyncio.start_unix_server(unix_client_connected, path=f"{vsock_path}_52")
        os.system(f"chown 1000:1000 {jailer_path}/tmp/v.sock_52")
        await queue.get()

        print("ready")

        while True:
            data = input("Send some data ? ")
            reader, writer = await asyncio.open_unix_connection(path=vsock_path)
            writer.write(('CONNECT 52\n' + data + '\n').encode())
            await writer.drain()

            ack = await reader.readline()
            print('ack=', ack)
            response = await reader.read()
            print(f'<<<\n{response.decode()}>>>')
            writer.close()
            await writer.wait_closed()

    finally:
        if proc:
            proc.terminate()
            proc.kill()
        # if os.path.exists(path=socket_path):
        #     os.remove(path=socket_path)


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
