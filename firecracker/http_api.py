import asyncio
from os import system

import aiohttp
from aiohttp import web

from firecracker.vm import MicroVM, setfacl

pool = asyncio.Queue()
counter = 4

ALEPH_API_SERVER = "https://api2.aleph.im"

async def index(request: web.Request):
    return web.Response(text="Hello, world")


async def get_new_vm() -> MicroVM:
    global counter
    vm_id = counter
    counter += 1
    print('Created VM=', vm_id)
    await setfacl()
    vm = MicroVM(vm_id)
    vm.cleanup_jailer()
    await vm.start_jailed_firecracker()
    await vm.socket_is_ready()
    await vm.set_boot_source('vmlinux.bin')
    await vm.set_rootfs('disks/rootfs.ext4')
    await vm.set_vsock()
    await vm.set_network()
    await asyncio.gather(
        vm.start_instance(),
        vm.wait_for_init()
    )
    return vm


async def register_new_vm():
    global pool
    vm = await get_new_vm()
    await pool.put(vm)
    return vm


async def get_a_vm():
    global pool
    # Create a new VM first to balance the pool
    loop = asyncio.get_event_loop()
    loop.create_task(register_new_vm())
    # Return the first VM from the pool
    return await pool.get()


async def run_code(request: web.Request):
    data = await request.post()
    code = data['code']
    vm = await get_a_vm()
    print("Using vm=", vm.vm_id)
    result = {
        'output': (await vm.run_code(code)).decode()
    }
    await vm.stop()
    system(f"rm -fr {vm.jailer_path}")
    return web.json_response(result)


async def run_code_from_post(request: web.Request):
    address = request.match_info['address']
    url = f"{ALEPH_API_SERVER}/api/v0/posts.json?addresses={address}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            print(resp.status)
            data = await resp.json()
    code = data['posts'][0]['content']['content']['code']

    vm = await get_a_vm()
    print("Using vm=", vm.vm_id)
    result = await vm.run_code(code)
    await vm.stop()
    system(f"rm -fr {vm.jailer_path}")

    return web.Response(body=result, content_type='text/plain', charset='UTF-8')


app = web.Application()
app.add_routes([web.get('/', index)])
app.add_routes([web.post('/run/code', run_code)])
app.add_routes([web.get('/run/post/{address}', run_code_from_post)])

def run():
    loop = asyncio.get_event_loop()
    for i in range(5):
        loop.create_task(register_new_vm())
    print('webapp')
    web.run_app(app)
