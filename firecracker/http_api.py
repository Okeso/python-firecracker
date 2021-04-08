import asyncio
from os import system

import aiohttp
from aiohttp import web

from firecracker.vm import MicroVM, setfacl


async def index(request: aiohttp.web.Request):
    return web.Response(text="Hello, world")


async def get_new_vm() -> MicroVM:
    vm_id = '123456'
    await setfacl()
    vm = MicroVM(vm_id)
    vm.cleanup_jailer()
    await vm.start_jailed_firecracker()
    await asyncio.sleep(1)
    await vm.set_boot_source('hello-vmlinux.bin')
    await vm.set_rootfs('disks/rootfs.ext4')
    await vm.set_vsock()
    await vm.set_network()
    await asyncio.gather(
        vm.start_instance(),
        vm.wait_for_init()
    )
    return vm


async def run_code(request: aiohttp.web.Request):
    data = await request.post()
    code = data['code']
    vm = await get_new_vm()
    result = {
        'output': (await vm.run_code(code)).decode()
    }
    await vm.stop()
    system(f"rm -fr {vm.jailer_path}")
    return web.json_response(result)


app = web.Application()
app.add_routes([web.get('/', index)])
app.add_routes([web.post('/run/code', run_code)])


def run():
    web.run_app(app)
