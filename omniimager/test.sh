#!/bin/bash

dd if=/dev/zero of=${1} bs=1M count=2000
fdisk ${1} << EOF
n
p



w
EOF

