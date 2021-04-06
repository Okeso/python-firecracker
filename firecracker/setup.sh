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

