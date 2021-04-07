wget "https://s3.amazonaws.com/spec.ccfc.min/img/hello/fsfiles/hello-rootfs.ext4"

e2fsck -f hello-rootfs.ext4

resize2fs hello-rootfs.ext4 1000000

vi /etc/ssh/sshd_config

echo "nameserver 8.8.8.8" >> /etc/resolv.conf

apk update
apk add build-base
apk add linux-headers # for vm_sockets.h

wget "https://raw.githubusercontent.com/stefanha/nc-vsock/master/nc-vsock.c"
cc nc-vsock.c -o nc-vsock

apk add python3

# Upgrade Alpine to 3.13
# https://wiki.alpinelinux.org/wiki/Upgrading_Alpine

createuser jailer
./jailer-v0.24.2-x86_64 --id 551e7604-e35c-42b3-b825-416853441234 --exec-file /root/python-firecracker/firecracker.bin --uid 1000 --gid 1000
