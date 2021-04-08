import asyncio
from functools import lru_cache
from os import system, getuid
import os.path
from pathlib import Path
from shutil import copyfile

import aiohttp
from aiohttp import ClientResponse


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


class MicroVM:
    vm_id: str
    proc: asyncio.subprocess.Process

    @property
    def jailer_path(self):
        return f"/srv/jailer/firecracker.bin/{self.vm_id}/root"

    @property
    def socket_path(self):
        return f"{self.jailer_path}/run/firecracker.socket"

    @property
    def vsock_path(self):
        return f"{self.jailer_path}/tmp/v.sock"

    def __init__(self, vm_id: str):
        self.vm_id = vm_id

    @lru_cache()
    def get_session(self) -> aiohttp.ClientSession:
        conn = aiohttp.UnixConnector(path=self.socket_path)
        return aiohttp.ClientSession(connector=conn)

    def cleanup_jailer(self):
        system(f"rm -fr {self.jailer_path}/run/")
        system(f"rm -fr {self.jailer_path}/dev/")

        if os.path.exists(path=self.vsock_path):
            os.remove(path=self.vsock_path)

        system(f"mkdir -p {self.jailer_path}/tmp/")
        system(f"chown jailman:jailman {self.jailer_path}/tmp/")

        system(f"mkdir -p {self.jailer_path}/opt")
        system(f"cp disks/rootfs.ext4 {self.jailer_path}/opt")
        # system(f"cp hello-vmlinux.bin {self.jailer_path}/opt")

    async def start_jailed_firecracker(self) -> asyncio.subprocess.Process:
        self.proc = await asyncio.create_subprocess_exec(
            './jailer-v0.24.2-x86_64',
            "--id", self.vm_id, "--exec-file", "/root/python-firecracker/firecracker.bin",
            "--uid", "1000", "--gid", "1000",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        return self.proc

    async def set_boot_source(self, kernel_image_path: str):
        kernel_filename = Path(kernel_image_path).name
        jailer_kernel_image_path = f"/opt/{kernel_filename}"
        copyfile(kernel_image_path, f"{self.jailer_path}{jailer_kernel_image_path}")
        data = {
            "kernel_image_path": jailer_kernel_image_path,
            "boot_args": "console=ttyS0 reboot=k panic=1 pci=off",
        }
        session = self.get_session()
        response: ClientResponse = await session.put(
            'http://localhost/boot-source',
            json=data)
        print(response)
        print([await response.text()])
        response.raise_for_status()

    async def set_rootfs(self, path_on_host: str):
        rootfs_filename = Path(path_on_host).name
        jailer_path_on_host = f"/opt/{rootfs_filename}"
        copyfile(path_on_host, f"{self.jailer_path}{rootfs_filename}")
        data = {
            "drive_id": "rootfs",
            "path_on_host": jailer_path_on_host,
            "is_root_device": True,
            "is_read_only": True,
        }
        session = self.get_session()
        response = await session.put('http://localhost/drives/rootfs',
                                     json=data)
        print(response)
        print([await response.text()])
        response.raise_for_status()

    async def set_vsock(self):
        data = {
            "vsock_id": "1",
            "guest_cid": 3,
            "uds_path": "/tmp/v.sock",
        }
        session = self.get_session()
        response = await session.put('http://localhost/vsock',
                                     json=data)
        print(response)
        print([await response.text()])
        response.raise_for_status()

    async def set_network(self):
        data = {
            "iface_id": "eth0",
            "guest_mac": "AA:FC:00:00:00:01",
            "host_dev_name": "tap0",
        }
        session = self.get_session()
        response = await session.put('http://localhost/network-interfaces/eth0',
                                     json=data)
        print(response)
        print([await response.text()])
        response.raise_for_status()

    async def start_instance(self):
        data = {
            "action_type": "InstanceStart",
        }
        session = self.get_session()
        response = await session.put('http://localhost/actions',
                                     json=data)
        print(response)
        print([await response.text()])
        response.raise_for_status()

    async def wait_for_init(self):
        """Wait for a connection from the init in the VM"""
        print("Waiting for signal")
        queue = asyncio.Queue()

        async def unix_client_connected(*args):
            print('args', args)
            await queue.put(True)

        await asyncio.start_unix_server(unix_client_connected, path=f"{self.vsock_path}_52")
        os.system(f"chown 1000:1000 {self.jailer_path}/tmp/v.sock_52")
        await queue.get()
        print("signal received")

    async def run_code(self, code: str):
        reader, writer = await asyncio.open_unix_connection(path=self.vsock_path)
        writer.write(('CONNECT 52\n' + code + '\n').encode())
        await writer.drain()

        ack = await reader.readline()
        print('ack=', ack)
        response = await reader.read()
        print(f'<<<\n{response.decode()}>>>')
        writer.close()
        await writer.wait_closed()
        return response

    def stop(self):
        if self.proc:
            self.proc.terminate()
            self.proc.kill()

    def __del__(self):
        self.stop()
