import asyncio
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect

import serial_console
import ssh_console
import vm


@asynccontextmanager
async def lifespan(app):
    # при старте сервера запускаем фоновое чтение serial-порта
    task = asyncio.create_task(serial_console.reader_loop())
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan)


@app.post("/api/vm/start")
def start():
    vm.start()
    return vm.status()


@app.post("/api/vm/reboot")
def reboot():
    try:
        vm.reboot()
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return vm.status()


@app.post("/api/vm/stop")
def stop():
    vm.stop()
    return vm.status()


@app.get("/api/vm/status")
def status():
    return vm.status()


@app.websocket("/ws/serial")
async def ws_serial(ws: WebSocket):
    await ws.accept()
    # сначала отдаём накопленный вывод, потом подписываем на новый
    if serial_console.buffer:
        # вырезаем из истории запросы позиции курсора,
        # иначе терминал отвечает на них повторно и в ВМ попадает мусор
        await ws.send_bytes(serial_console.buffer.replace(b"\x1b[6n", b""))
    serial_console.clients.add(ws)
    try:
        while True:
            msg = json.loads(await ws.receive_text())
            if msg["type"] == "input":
                serial_console.send(msg["data"].encode())
    except WebSocketDisconnect:
        pass
    finally:
        serial_console.clients.discard(ws)


@app.websocket("/ws/ssh")
async def ws_ssh(ws: WebSocket):
    await ws.accept()
    try:
        await ssh_console.handle(ws)
    except (WebSocketDisconnect, RuntimeError):
        pass  # клиент закрыл вкладку или сессия завершилась
