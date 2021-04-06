import asyncio
import os
import sys
import time

import aiohttp
from aiohttp import ClientResponse
from os import getuid


arch='x86_64'
dest_kernel="hello-vmlinux.bin"
dest_rootfs="disks/rootfs.ext4"
# image_bucket_url="https://s3.amazonaws.com/spec.ccfc.min/img"


async def net_create_tap():
    name = "tap0"
    os.system(f"sudo ip tuntap add {name} mode tap")

    os.system("ip addr add 172.16.0.1/24 dev tap0")
    os.system("ip link set tap0 up")
    os.system('sh -c "echo 1 > /proc/sys/net/ipv4/ip_forward"')
    os.system("iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE")
    os.system("iptables -A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT")
    os.system("iptables -A FORWARD -i tap0 -o eth0 -j ACCEPT")


async def setfacl():
    user = getuid()
    cmd = f"sudo setfacl -m u:{user}:rw /dev/kvm"
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()

    print(f'[{cmd!r} exited with {proc.returncode}]')
    if stdout:
        print(f'[stdout]\n{stdout.decode()}')
    if stderr:
        print(f'[stderr]\n{stderr.decode()}')


async def start_firecracker():
    cmd = "./firecracker.bin --api-sock /tmp/firecracker.socket"
    proc = await asyncio.create_subprocess_exec(
        './firecracker.bin',
        "--api-sock", "/tmp/firecracker.socket",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    # stdout, stderr = await proc.communicate()

    # print(f'[{cmd!r} exited with {proc.returncode}]')
    # if stdout:
    #     print(f'[stdout]\n{stdout.decode()}')
    # if stderr:
    #     print(f'[stderr]\n{stderr.decode()}')
    return proc


async def set_kernel(session: aiohttp.ClientSession):
    data = {
        "kernel_image_path": dest_kernel,
        "boot_args": "console=ttyS0 reboot=k panic=1 pci=off",
    }
    response: ClientResponse = await session.put('http://localhost/boot-source',
                                 json=data)
    print(response)
    print([response.text])


async def set_rootfs(session: aiohttp.ClientSession):
    data = {
        "drive_id": "rootfs",
        "path_on_host": dest_rootfs,
        "is_root_device": True,
        "is_read_only": False,
    }
    response = await session.put('http://localhost/drives/rootfs',
                                 json=data)
    print(response)
    print([response.text])


async def set_vsock(session: aiohttp.ClientSession):
    if os.path.exists(path='/tmp/v.sock'):
        os.remove(path='/tmp/v.sock')
    data = {
        "vsock_id": "1",
        "guest_cid": 3,
        "uds_path": "/tmp/v.sock"
    }
    response = await session.put('http://localhost/vsock',
                                 json=data)
    print(response)
    print([response.text])


async def set_network(session: aiohttp.ClientSession):
    data = {
        "iface_id": "eth0",
        "guest_mac": "AA:FC:00:00:00:01",
        "host_dev_name": "tap0",
    }
    response = await session.put('http://localhost/network-interfaces/eth0',
                                 json=data)
    print(response)
    print([response.text])


async def start_machine(session: aiohttp.ClientSession):
    data = {
        "action_type": "InstanceStart",
    }
    response = await session.put('http://localhost/actions',
                                 json=data)
    print(response)
    print([response.text])

async def main():
    await setfacl()

    proc = None
    try:
        print("./firecracker.bin --api-sock /tmp/firecracker.socket")
        if not input("Using existing Firecracker here ?"):
            if os.path.exists(path='/tmp/firecracker.socket'):
                os.remove(path='/tmp/firecracker.socket')
            proc = await start_firecracker()
            print("Waiting a bit...")
            await asyncio.sleep(2)
            print("Waited")
        else:
            proc = None

        conn = aiohttp.UnixConnector(path='/tmp/firecracker.socket')
        session = aiohttp.ClientSession(connector=conn)
        await set_kernel(session)

        await set_rootfs(session)

        await set_network(session)

        await set_vsock(session)

        await start_machine(session)

        print("Waiting for start")
        signal = b"MANAGER READY"
        while True:
            line = await proc.stdout.readline()
            print('|', line.decode().strip())
            if signal in line:
                break
        print("ready")

        while True:
            data = input("Send some data ? ")
            reader, writer = await asyncio.open_unix_connection(path='/tmp/v.sock')
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
        if os.path.exists(path='/tmp/firecracker.socket'):
            os.remove(path='/tmp/firecracker.socket')


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
