import asyncio
import os
from os import getuid

import aiohttp
from aiohttp import ClientResponse

arch='x86_64'
dest_kernel="/opt/hello-vmlinux.bin"
dest_rootfs="/opt/rootfs.ext4"
vm_id = "551e7604-e35c-42b3-b825-416853441234"
jailer_path = f"/srv/jailer/firecracker.bin/{vm_id}/root"
socket_path = f"{jailer_path}/run/firecracker.socket"
vsock_path = f"{jailer_path}/tmp/v.sock"
# image_bucket_url="https://s3.amazonaws.com/spec.ccfc.min/img"
# socket_path = "/tmp/firecracker.socket"
# vsock_path = "/tmp/v.sock"


async def set_kernel(session: aiohttp.ClientSession):
    data = {
        "kernel_image_path": dest_kernel,
        "boot_args": "console=ttyS0 reboot=k panic=1 pci=off",
    }
    response: ClientResponse = await session.put('http://localhost/boot-source',
                                 json=data)
    print(response)
    print([await response.text()])


async def set_rootfs(session: aiohttp.ClientSession):
    data = {
        "drive_id": "rootfs",
        "path_on_host": dest_rootfs,
        "is_root_device": True,
        "is_read_only": True,
    }
    response = await session.put('http://localhost/drives/rootfs',
                                 json=data)
    print(response)
    print([await response.text()])


async def set_vsock(session: aiohttp.ClientSession):
    if os.path.exists(path=vsock_path):
        os.remove(path=vsock_path)
    data = {
        "vsock_id": "1",
        "guest_cid": 3,
        "uds_path": "/tmp/v.sock",
    }
    response = await session.put('http://localhost/vsock',
                                 json=data)
    print(response)
    text = await response.text()
    print(text)
    print('---')


async def set_network(session: aiohttp.ClientSession):
    data = {
        "iface_id": "eth0",
        "guest_mac": "AA:FC:00:00:00:01",
        "host_dev_name": "tap0",
    }
    response = await session.put('http://localhost/network-interfaces/eth0',
                                 json=data)
    print(response)
    print([await response.text()])


def configure_vm(session: aiohttp.ClientSession):
    return asyncio.gather(
        set_kernel(session),
        set_rootfs(session),
        set_network(session),
        set_vsock(session),
    )


async def net_create_tap():
    name = "tap0"
    os.system(f"sudo ip tuntap add {name} mode tap")

    os.system("ip addr add 172.16.0.1/24 dev tap0")
    os.system("ip link set tap0 up")
    os.system('sh -c "echo 1 > /proc/sys/net/ipv4/ip_forward"')
    os.system("iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE")
    os.system("iptables -A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT")
    os.system("iptables -A FORWARD -i tap0 -o eth0 -j ACCEPT")


def cleanup_jailer():
    os.system(f"rm -fr {jailer_path}/run/")
    os.system(f"rm -fr {jailer_path}/dev/")

    os.system(f"mkdir -p {jailer_path}/tmp/")
    os.system(f"chown jailman:jailman {jailer_path}/tmp/")

    os.system(f"mkdir -p {jailer_path}/opt")
    os.system(f"cp disks/rootfs.ext4 {jailer_path}/opt")
    os.system(f"cp hello-vmlinux.bin {jailer_path}/opt")


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


async def start_jailed_firecracker():
    proc = await asyncio.create_subprocess_exec(
        './jailer-v0.24.2-x86_64',
        "--id", vm_id, "--exec-file", "/root/python-firecracker/firecracker.bin",
        "--uid", "1000", "--gid", "1000",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    return proc


async def start_machine(session: aiohttp.ClientSession):
    data = {
        "action_type": "InstanceStart",
    }
    response = await session.put('http://localhost/actions',
                                 json=data)
    print(response)
    print([await response.text()])
