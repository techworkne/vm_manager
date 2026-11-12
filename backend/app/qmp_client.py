import json
import socket


def connect(path):
    """Подключение к qmp. чтение приветсвие"""
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(path)
    f = sock.makefile("rw")
    greetings = json.loads(f.readline())
    print(f"Version of QEMU: {greetings['QMP']['version']['qemu']}")
    return f


def execute(f, command, args=None):
    """Отправление команды"""
    msg = {"execute": command}
    if args:
        msg["arguments"] = args

    f.write(json.dumps(msg) + "\n")
    f.flush()

    while True:
        line = f.readline()
        if not line:
            raise ConnectionError()
        reply = json.loads(line)
        if "event" in reply:
            print(reply["event"])
            continue
        if "error" in reply:
            raise RuntimeError(reply["error"]["desc"])
        if "return" in reply:
            return reply["return"]
