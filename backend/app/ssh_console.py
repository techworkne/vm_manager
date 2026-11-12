import asyncio
import json
import os

import asyncssh

SSH_HOST = "127.0.0.1"
SSH_PORT = 2222
SSH_USER = "user"
SSH_KEY = os.environ.get("SSH_KEY", "keys/vm_key")


async def connect(ws):
    """Подключение по SSH с повторами, пока ВМ загружается"""
    await ws.send_bytes("Подключение по SSH...".encode())
    for _ in range(150):  # не меньше 5 минут: без KVM ВМ грузится долго
        try:
            return await asyncssh.connect(
                SSH_HOST, SSH_PORT,
                username=SSH_USER,
                client_keys=[SSH_KEY],
                known_hosts=None,
                login_timeout=10,
            )
        except (OSError, asyncssh.Error, asyncio.TimeoutError):
            # sshd ещё не готов -- рисуем точку и ждём
            await ws.send_bytes(b".")
            await asyncio.sleep(2)
    return None


async def pump_output(process, ws):
    """Пересылка вывода из SSH в браузер"""
    while True:
        data = await process.stdout.read(4096)
        if not data:
            break
        await ws.send_bytes(data)
    await ws.close()


async def handle(ws):
    """Одна SSH-сессия для одного WebSocket-клиента"""
    conn = await connect(ws)
    if conn is None:
        await ws.send_bytes("\r\nНе удалось подключиться по SSH\r\n".encode())
        return
    await ws.send_bytes(b"\r\n")

    async with conn:
        process = await conn.create_process(
            term_type="xterm-256color",
            term_size=(80, 24), # начальный размер, браузер потом пришлёт свой
            encoding=None,
        )
        task = asyncio.create_task(pump_output(process, ws))
        try:
            while True:
                msg = json.loads(await ws.receive_text())
                if msg["type"] == "input":
                    process.stdin.write(msg["data"].encode())
                elif msg["type"] == "resize":
                    process.change_terminal_size(msg["cols"], msg["rows"])
        finally:
            task.cancel()
