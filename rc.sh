#!/bin/sh

echo "=== My Bash RC ==="

#ls /
#ls /dev
#
#mkdir /dev/pts
#mkdir /dev/shm
#
#mount -t proc proc /proc -o nosuid,noexec,nodev
#mount -t sysfs sys /sys -o nosuid,noexec,nodev
#mount -t tmpfs run /run -o mode=0755,nosuid,nodev
##mount -t devtmpfs dev /dev -o mode=0755,nosuid
#mount -t devpts devpts /dev/pts -o mode=0620,gid=5,nosuid,noexec
#mount -t tmpfs shm /dev/shm -omode=1777,nosuid,nodev


sleep 0.5
sync

ip addr add 172.16.0.2/24 dev eth0
ip link set eth0 up
ip route add default via 172.16.0.1 dev eth0
sync

ip addr

echo "Net up"

/usr/sbin/sshd -de

echo "SSH UP"

python3 --version
/root/manager.py

ps aux

echo "SLEEP 6000"
sleep 6000

echo "EXIT"
reboot

sleep 5

