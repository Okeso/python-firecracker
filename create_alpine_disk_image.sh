#!/bin/sh
#
#dest_rootfs="disks/hello-rootfs.ext4"
#image_bucket_url="https://s3.amazonaws.com/spec.ccfc.min/img"
#
#rootfs="${image_bucket_url}/hello/fsfiles/hello-rootfs.ext4"
#
#echo "Downloading $rootfs..."
#curl -fsSL -o $dest_rootfs $rootfs
#
#e2fsck -f disks/hello-rootfs.ext4
#
#resize2fs disks/hello-rootfs.ext4 1000000
#
#mount disks/hello-rootfs.ext4 /mnt/rootfs

mkdir -p disks
curl -fsSL -o disks/alpine-miniroot.tgz https://dl-cdn.alpinelinux.org/alpine/v3.13/releases/x86_64/alpine-minirootfs-3.13.3-x86_64.tar.gz

dd if=/dev/zero of=disks/rootfs.ext4 bs=1M count=1000
mkfs.ext4 disks/rootfs.ext4
mkdir -p /mnt/rootfs
mount disks/rootfs.ext4 /mnt/rootfs
tar --preserve-permissions --same-owner -xf  disks/alpine-miniroot.tgz --directory /mnt/rootfs

#vi /etc/ssh/sshd_config

echo "nameserver 8.8.8.8" >> /mnt/rootfs/etc/resolv.conf

#chroot /mnt/rootfs /bin/sh <<EOT
#apk update
#apk add build-base
#apk add linux-headers
#apk add python3
#EOT

#cat <<EOT > /mnt/rootfs/etc/apk/repositories
#http://dl-cdn.alpinelinux.org/alpine/v3.13/main
#http://dl-cdn.alpinelinux.org/alpine/v3.13/community
#EOT

#chroot /mnt/rootfs /bin/sh <<EOT
#apk add busybox-static apk-tools-static
#apk.static update
#apk.static upgrade --no-self-upgrade --available
#EOT

chroot /mnt/rootfs /bin/sh <<EOT
#apk add openrc
#apk add util-linux
apk add python3
#
## Set up a login terminal on the serial console (ttyS0):
ln -s agetty /etc/init.d/agetty.ttyS0
echo ttyS0 > /etc/securetty
#rc-update add agetty.ttyS0 default
#
## Make sure special file systems are mounted on boot:
#rc-update add devfs boot
#rc-update add procfs boot
#rc-update add sysfs boot
EOT

cat <<EOT > /mnt/rootfs/etc/inittab
# /etc/inittab

::sysinit:/sbin/myrc sysinit
::sysinit:/sbin/myrc boot
::wait:/sbin/myrc default

# Set up a couple of getty's
tty1::respawn:/sbin/getty 38400 tty1
tty2::respawn:/sbin/getty 38400 tty2
tty3::respawn:/sbin/getty 38400 tty3
tty4::respawn:/sbin/getty 38400 tty4
tty5::respawn:/sbin/getty 38400 tty5
tty6::respawn:/sbin/getty 38400 tty6

# Put a getty on the serial port
ttyS0::respawn:/sbin/getty -L ttyS0 115200 vt100

# Stuff to do for the 3-finger salute
::ctrlaltdel:/sbin/reboot

# Stuff to do before rebooting
::shutdown:/sbin/myrc shutdown

EOT

# Custom init
cp /mnt/rootfs/sbin/init /mnt/rootfs/sbin/init.orig
cp rc.sh /mnt/rootfs/sbin/myrc
cp manager.py /mnt/rootfs/root/manager.py
chmod +x /mnt/rootfs/sbin/myrc
chmod +x /mnt/rootfs/root/manager.py

umount /mnt/rootfs

# linux-headers for vm_sockets.h
# busybox-static apk-tools-static to upgrade

#wget "https://raw.githubusercontent.com/stefanha/nc-vsock/master/nc-vsock.c"
#cc nc-vsock.c -o nc-vsock

# Upgrade Alpine to 3.13
# https://wiki.alpinelinux.org/wiki/Upgrading_Alpine

