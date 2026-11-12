import asyncio

from vm import SERIAL_SOCK

BUFFER_SIZE = 64 * 1024

buffer = b""  # последний вывод ВМ, чтобы новый клиент видел историю
clients = set()
writer = None


async def reader_loop():
    """Фоновая задача: читает serial-сокет и рассылает вывод клиентам"""
    global buffer, writer
    while True:
        try:
            reader, writer = await asyncio.open_unix_connection(SERIAL_SOCK)
        except OSError:
            # ВМ ещё не запущена -- попробуем позже
            await asyncio.sleep(1)
            continue

        try:
            while True:
                data = await reader.read(4096)
                if not data:  # QEMU закрыл сокет -- ВМ остановлена
                    break
                buffer = (buffer + data)[-BUFFER_SIZE:]
                for ws in list(clients):
                    try:
                        await ws.send_bytes(data)
                    except Exception:
                        clients.discard(ws)
        except OSError:
            pass

        writer.close()
        writer = None
        await asyncio.sleep(1)


def send(data):
    """Отправка ввода пользователя в ВМ"""
    if writer is not None:
        writer.write(data)
