#!/bin/bash

dd if=/dev/zero of=${1} bs=1M count=4000
mknod /dev/loop100 b 7 100
fdisk ${1} << EOF
n
p



w
EOF

losetup /dev/loop100 -o 1048576 ${1}
mkfs.ext4 /dev/loop100
mount -t ext4 /dev/loop7 ${2}