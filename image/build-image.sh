#!/bin/bash
set -e
cd "$(dirname "$0")/.."

BASE_IMAGE="debian-13-genericcloud-amd64-20261001-2618.qcow2"
IMAGE_URL="https://cloud.debian.org/images/cloud/trixie/20261001-2618/$BASE_IMAGE"

mkdir -p vm keys

if [ ! -f "vm/$BASE_IMAGE" ]; then
    echo "Скачивание базового образа"
    # качаем во временный файл, чтобы оборванная загрузка не считалась готовой
    wget -O "vm/$BASE_IMAGE.part" "$IMAGE_URL"
    mv "vm/$BASE_IMAGE.part" "vm/$BASE_IMAGE"
fi

if [ ! -f keys/vm_key ]; then
    echo "SSH-ключ не найденю Создание нового."
    ssh-keygen -t ed25519 -f keys/vm_key -N ""
fi

sed "s|__SSH_PUBLIC_KEY__|$(cat keys/vm_key.pub)|" image/user-data.template > vm/user-data

# seed.iso для cloud-init: метка тома обязательно cidata
genisoimage -quiet -output vm/seed.iso -volid cidata -joliet -rock vm/user-data image/meta-data

echo "Создание диска ВМ"
rm -f vm/vm.qcow2
qemu-img create -f qcow2 -b "$BASE_IMAGE" -F qcow2 vm/vm.qcow2 10G

echo "Готово: образ в папке vm/"
