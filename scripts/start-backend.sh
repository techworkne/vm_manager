#!/bin/bash
# при первом старте собирает образ ВМ, затем поднимает сервер
set -e
cd "$(dirname "$0")/.."

if [ ! -f vm/vm.qcow2 ]; then
    echo "Образ ВМ не найден. Запуск сборки."
    bash image/build-image.sh
fi

exec uvicorn main:app --app-dir backend/app --host 0.0.0.0 --port 8000
