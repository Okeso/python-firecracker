
rm -fr /srv/jailer/firecracker.bin/551e7604-e35c-42b3-b825-416853441234/root/run/
rm -fr /srv/jailer/firecracker.bin/551e7604-e35c-42b3-b825-416853441234/root/dev/

mkdir -p /srv/jailer/firecracker.bin/551e7604-e35c-42b3-b825-416853441234/root/tmp/
chown jailman:jailman /srv/jailer/firecracker.bin/551e7604-e35c-42b3-b825-416853441234/root/tmp/

mkdir -p /srv/jailer/firecracker.bin/551e7604-e35c-42b3-b825-416853441234/root/opt
cp disks/rootfs.ext4 /srv/jailer/firecracker.bin/551e7604-e35c-42b3-b825-416853441234/root/opt
cp hello-vmlinux.bin /srv/jailer/firecracker.bin/551e7604-e35c-42b3-b825-416853441234/root/opt
