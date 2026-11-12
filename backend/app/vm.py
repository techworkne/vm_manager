import os
import subprocess
import threading
import time

import qmp_client

VM_DIR = os.environ.get("VM_DIR", "vm")
QMP_SOCK = f"{VM_DIR}/qmp.sock"
SERIAL_SOCK = f"{VM_DIR}/serial.sock"

process = None
qmp = None
lock = threading.Lock()


def build_command():
    if os.access("/dev/kvm", os.W_OK):
        accel = ["-accel", "kvm", "-cpu", "host"]
    else:
        accel = ["-accel", "tcg", "-cpu", "max"]
    return [
        "qemu-system-x86_64", "-machine", "q35", *accel,
        "-m", "1024", "-smp", "2",
        "-drive", f"file={VM_DIR}/vm.qcow2,if=virtio,format=qcow2",
        "-drive", f"file={VM_DIR}/seed.iso,if=virtio,format=raw,readonly=on",
        "-netdev", "user,id=n0,hostfwd=tcp::2222-:22",
        "-device", "virtio-net-pci,netdev=n0",
        "-qmp", f"unix:{QMP_SOCK},server=on,wait=off",
        "-chardev", f"socket,id=ser0,path={SERIAL_SOCK},server=on,wait=off",
        "-serial", "chardev:ser0",
        "-display", "none",
        "-S",
    ]


def is_running():
    return process is not None and process.poll() is None


def start():
    global process, qmp
    with lock:
        if is_running():
            return
        if os.path.exists(QMP_SOCK):
            try:
                os.remove(QMP_SOCK)
            except Exception as e:
                print(f"Не вышло удалить старый {QMP_SOCK}. Ошибка: {e}")

        process = subprocess.Popen(build_command())
        for _ in range(50):
            if not os.path.exists(QMP_SOCK):
                time.sleep(0.1)
            else:
                break

        qmp = qmp_client.connect(QMP_SOCK)
        qmp_client.execute(qmp, "qmp_capabilities")
        qmp_client.execute(qmp, "cont")



def reboot():
    with lock:
        if not is_running():
            raise RuntimeError("ВМ не запущена")
        qmp_client.execute(qmp, "system_reset")



def stop():
    global process, qmp
    with lock:
        if not is_running():
            return
        qmp_client.execute(qmp, "system_powerdown")

        try:
            process.wait(timeout=30)
        except subprocess.TimeoutExpired:# не выключилась за 30 сек
            try:
                qmp_client.execute(qmp, "quit") # грубой отключение
            except ConnectionError:
                pass
            process.wait()


        process = None
        qmp = None


def status():
    with lock:
        if not is_running():
            return {"running": False, "status": "stopped"}
        else:
            res = qmp_client.execute(qmp, "query-status")
            return {"running": res["running"], "status": res["status"]}
