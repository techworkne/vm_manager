import { useEffect, useRef } from 'react'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import '@xterm/xterm/css/xterm.css'


export default function Console({ mode }) {
  const boxRef = useRef(null)

  useEffect(() => {
    const term = new Terminal({ cursorBlink: true, fontSize: 14 })
    const fit = new FitAddon()
    term.loadAddon(fit)
    term.open(boxRef.current)
    fit.fit() // подгоняем размер терминала под блок на странице

    const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
    const ws = new WebSocket(`${protocol}://${location.host}/ws/${mode}`)
    ws.binaryType = 'arraybuffer' // backend шлёт байты

    function send(message) {
      if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(message))
    }

    ws.onopen = () => send({ type: 'resize', cols: term.cols, rows: term.rows })
    ws.onmessage = (event) => term.write(new Uint8Array(event.data))
    ws.onclose = () => term.write('\r\n\x1b[33m[соединение закрыто]\x1b[0m\r\n')


    const onData = term.onData((data) => send({ type: 'input', data }))
    const onResize = term.onResize(({ cols, rows }) => send({ type: 'resize', cols, rows }))

    const onWindowResize = () => fit.fit()
    window.addEventListener('resize', onWindowResize)
    term.focus()

    return () => {
      window.removeEventListener('resize', onWindowResize)
      onData.dispose()
      onResize.dispose()
      ws.onclose = null
      ws.close()
      term.dispose()
    }
  }, [mode])

  return <div className="console" ref={boxRef}></div>
}
