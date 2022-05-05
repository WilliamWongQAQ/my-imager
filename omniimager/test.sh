#!/bin/bash

dd if=/dev/zero of=${1} bs=1M count=3000
fdisk ${1} << EOF
n
p



w
EOF

losetup /dev/loop7 -o 1572864 /opt/omni-workspace/test.raw
mkfs.ext4 /dev/loop7
mount -t ext4 /dev/loop7 ${2}
