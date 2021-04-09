# (WIP) HTTP service to run Python code in Firecracker VMs

> Note: This is still early prototyping.

This project provides a service that runs untrusted Python code in Firecracker
"micro virtual machines".

## Running

Clone this reposotiry on the host machine and run `./host_setup.sh` to configure it.

```shell
git clone https://github.com/Okeso/python-firecracker.git



```

Then run:
```shell
export PYTHONPATH=$(pwd)
python3 firecracker/__main__.py
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
