#!/bin/bash
set -e
cd "$(dirname "$0")/.."

if [ -w /dev/kvm ]; then
    ACCEL="-accel kvm -cpu host"
else
    ACCEL="-accel tcg -cpu max"
    echo "kvm недоступен. Запуск в режиме эмуляции TCG -- будет медленно."
fi    

qemu-system-x86_64 \
  -machine q35 $ACCEL \
  -m 1024 -smp 2 \
  -drive file=vm/vm.qcow2,if=virtio,format=qcow2 \
  -drive file=vm/seed.iso,if=virtio,format=raw,readonly=on \
  -netdev user,id=n0,hostfwd=tcp::2222-:22 \
  -device virtio-net-pci,netdev=n0 \
  -qmp unix:vm/qmp.sock,server=on,wait=off \
  -nographic