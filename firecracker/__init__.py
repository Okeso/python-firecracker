import asyncio
import os
import time

import aiohttp
from aiohttp import ClientResponse
from os import getuid


arch='x86_64'
dest_kernel="hello-vmlinux.bin"
dest_rootfs="disks/hello-rootfs.ext4"
# image_bucket_url="https://s3.amazonaws.com/spec.ccfc.min/img"


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
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
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
    if os.path.exists(path='/tmp/firecracker.socket'):
        os.remove(path='/tmp/firecracker.socket')
    try:
        print("./firecracker.bin --api-sock /tmp/firecracker.socket")
        if input("Start Firecracker here ?"):
            proc = await start_firecracker()
            await asyncio.sleep(3)

        conn = aiohttp.UnixConnector(path='/tmp/firecracker.socket')
        session = aiohttp.ClientSession(connector=conn)
        await set_kernel(session)

        await set_rootfs(session)

        await start_machine(session)

        input("Running...")

        proc.kill()
    finally:
        if os.path.exists(path='/tmp/firecracker.socket'):
            os.remove(path='/tmp/firecracker.socket')


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
