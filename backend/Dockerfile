# сборка QEMU 11.0.5
FROM debian:trixie-slim AS qemu-build

# компилятор и библиотеки, нужные для сборки QEMU
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential ca-certificates wget xz-utils pkg-config \
        python3 python3-venv ninja-build flex bison \
        libglib2.0-dev libpixman-1-dev libslirp-dev zlib1g-dev libfdt-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
# сервер загрузки иногда не отвечает. пробуем до 6 раз
RUN for i in 1 2 3 4 5 6; do \
        wget -4 -c -nv --tries=1 --timeout=20 https://download.qemu.org/qemu-11.0.5.tar.xz && break; \
        echo "Загрузка не удалась, попытка $i"; sleep 5; \
    done \
    && tar xf qemu-11.0.5.tar.xz \
    && rm qemu-11.0.5.tar.xz

WORKDIR /src/qemu-11.0.5
RUN ./configure --target-list=x86_64-softmmu --enable-slirp --enable-kvm --disable-docs \
    && make -j"$(nproc)" \
    && make install


# образ backend
FROM python:3.13-slim-trixie

RUN apt-get update && apt-get install -y --no-install-recommends \
        libglib2.0-0t64 libpixman-1-0 libslirp0 libfdt1 \
        wget ca-certificates openssh-client genisoimage \
    && rm -rf /var/lib/apt/lists/*

# готовый QEMU из первого этапа
# программы
COPY --from=qemu-build /usr/local/bin/qemu-system-x86_64 /usr/local/bin/qemu-img /usr/local/bin/
# служебные файлы
COPY --from=qemu-build /usr/local/share/qemu /usr/local/share/qemu

WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/app backend/app
COPY image image
COPY scripts scripts

# пути к файлам ВМ и SSH-ключу (обе папки -- тома в docker-compose.yml)
ENV VM_DIR=/app/vm
ENV SSH_KEY=/app/keys/vm_key

EXPOSE 8000
CMD ["bash", "scripts/start-backend.sh"]
