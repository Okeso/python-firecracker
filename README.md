# (WIP) HTTP service to run Python code in Firecracker VMs

> Note: This is still early prototyping.

This project provides a service that runs untrusted Python code in Firecracker
"micro virtual machines".

The following instructions are tested while running as root, either on bare metal or on a
VM that allows virtualisation (`/dev/kvm`) such as a DigitalOcean droplet.

## Running

Clone this reposotiry on the host machine and run `./host_setup.sh` to configure it.

```shell
apt update
apt -y upgrade
apt install -y git git-lfs python3 python3-aiohttp sudo acl curl systemd-container
useradd jailman
```

```shell
git clone https://github.com/Okeso/python-firecracker.git
cd python-firecracker/
# Make files available to all users
cp firecracker.bin /opt/firecracker.bin
cp vmlinux /opt/vmlinux.bin

bash create_alpine_disk_image.sh
# Not sure why yet, but run it once more \o/ 
bash create_alpine_disk_image.sh
cp disks/rootfs.ext4 /opt/rootfs.ext4

mkdir /srv/jailer
```

### Test Firecracker

```shell
./firecracker.bin --no-api --config-file vmconfig.json
````
If all goes well, this should end with a Python stacktrace:
`OSError: [Errno 97] Address family not supported by protocol`
followed by a Kernel panic stacktrace.

Then run:
```shell
export PYTHONPATH=$(pwd)
python3 -m firecracker
```

Test running code from an Aleph.im post on:
http://localhost:8080/run/post/0xb1142E1945E09d8C1F0CA708751407054d862D3e

Or HTTP POST your code on `http://localhost:8080/run/code/` in field `'code'` to get
the printed result.

## Compile your kernel

A lot of time at boot is saved by disabling keyboard support in the kernel.
See `dmesg` logs for the exact timing saved.

Start from https://github.com/firecracker-microvm/firecracker/blob/master/docs/rootfs-and-kernel-setup.md

Then disable:
`CONFIG_INPUT_KEYBOARD`
`CONFIG_INPUT_MISC`
`CONFIG_INPUT_FF_MEMLESS`
`CONFIG_SERIO`
