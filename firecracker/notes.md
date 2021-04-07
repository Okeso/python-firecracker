/etc/local.d/hello.start

https://docs.aws.amazon.com/enclaves/latest/user/nitro-enclave.html


# Todo

## ✓ Jailed

Use jailed to secure the VM

## Firewall

Isolate the VM from others.
Maybe force use of a VPN to get out. 

## Host APIs

Use aiohttp to expose API to clients that read the messages ?

Use aiohttp to expose features from the host ?
https://docs.aiohttp.org/en/v1.1.4/client.html#unix-domain-sockets 

## Custom kernel/initrd ?

Instead of the entropy Python script, use entropy from the CPU using a more recent Linux kernel.

https://github.com/marcov/firecracker-initrd

## Pool

Pool of VMs ready to be used for faster start.
Dynamic size could be interesting, keeping track
of host resources would be best.

## ✓ Read-only rootfs

Rootfs in squashfs
Overlay on tmpfs or other disk

```shell
/bin/mount -t tmpfs -o noatime,mode=0755 tmpfs /overlay
mkdir -p /overlay/root /overlay/work
/bin/mount -o noatime,lowerdir=/,upperdir=/overlay/root,workdir=/overlay/work -t overlay "overlayfs:/overlay/root" /mnt
mkdir -p /mnt/rom
pivot_root /mnt /mnt/rom
```

https://github.com/firecracker-microvm/firecracker-containerd/pull/153/files

