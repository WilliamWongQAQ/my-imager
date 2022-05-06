#!/bin/bash

dd if=/dev/zero of=${1} bs=1M count=4000

mkfs.ext4 ${1}
mount -o loop ${1} ${2}
