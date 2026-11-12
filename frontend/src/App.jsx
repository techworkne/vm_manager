import { useEffect, useState } from 'react'
import Console from './Console.jsx'

const STATUS_LABELS = {
  running: 'Работает',
  stopped: 'Остановлена',
  paused: 'На паузе',
  shutdown: 'Выключается',
}

export default function App() {
  const [status, setStatus] = useState(null) // ответ /api/vm/status
  const [offline, setOffline] = useState(false) // backend не отвечает
  const [error, setError] = useState('') // ошибка последней команды
  const [busy, setBusy] = useState(false) // идёт запрос, кнопки заблокированы
  const [mode, setMode] = useState('serial') // serial или ssh
  const [session, setSession] = useState(0) // меняем чтобы переподключить терминал

  async function loadStatus() {
    try {
      const res = await fetch('/api/vm/status')
      if (!res.ok) throw new Error()
      setStatus(await res.json())
      setOffline(false)
    } catch {
      setStatus(null)
      setOffline(true)
    }
  }


  useEffect(() => {
    loadStatus()
    const timer = setInterval(loadStatus, 2000)
    return () => clearInterval(timer)
  }, [])

  // отправка команды. start, reboot или stop
  async function sendCommand(command) {
    setBusy(true)
    setError('')
    try {
      const res = await fetch(`/api/vm/${command}`, { method: 'POST' })
      if (!res.ok) throw new Error()
      setStatus(await res.json())
      // старая SSH-сессия после команды уже не работает -- открываем новую
      if (mode === 'ssh') setSession(session + 1)
    } catch {
      setError('Не удалось выполнить команду')
    }
    setBusy(false)
  }

  const running = status !== null && status.status !== 'stopped'
  const label = status ? STATUS_LABELS[status.status] || status.status : 'Неизвестно'

  return (
    <div className="page">
      <header className="header">
        <h1>Виртуальная машина</h1>
        <div className="status">
          <span className={running ? 'dot dot-on' : 'dot'}></span>
          {label}
        </div>
      </header>

      <div className="toolbar">
        <button className="btn btn-start" disabled={busy || running} onClick={() => sendCommand('start')}>
          Включить
        </button>
        <button className="btn" disabled={busy || !running} onClick={() => sendCommand('reboot')}>
          Перезагрузить
        </button>
        <button className="btn btn-stop" disabled={busy || !running} onClick={() => sendCommand('stop')}>
          Остановить
        </button>
        {busy && <span className="hint">Выполняется...</span>}
        {offline && <span className="error">Backend недоступен</span>}
        {error && <span className="error">{error}</span>}
      </div>

      <div className="tabs">
        <button className={mode === 'serial' ? 'tab tab-active' : 'tab'} onClick={() => setMode('serial')}>
          Serial
        </button>
        <button className={mode === 'ssh' ? 'tab tab-active' : 'tab'} onClick={() => setMode('ssh')}>
          SSH
        </button>
        <button className="tab tab-right" onClick={() => setSession(session + 1)}>
          Переподключить
        </button>
      </div>

      <Console key={mode + session} mode={mode} />
    </div>
  )
}
